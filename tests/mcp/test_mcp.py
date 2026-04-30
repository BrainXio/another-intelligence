"""Tests for the MCP client, registry, and permissions integration."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from another_intelligence.events import MCPToolCalled, PostToolUse, PreToolUse
from another_intelligence.mcp.client import (
    MCPClient,
    MCPConnection,
    MCPRegistry,
    MCPServerConfig,
)
from another_intelligence.permissions.engine import (
    Grant,
    PermissionConfig,
    PermissionEngine,
)


class TestMCPRegistryDisciplineServers:
    """Registry discovery of ADHD, OCD, ASD discipline servers."""

    def test_loads_discipline_servers_from_config(self, tmp_path: Path):
        data = {
            "servers": [
                {
                    "name": "adhd",
                    "type": "stdio",
                    "command": "uv",
                    "args": ["run", "adhd-mcp"],
                    "permissions": ["adhd.*"],
                },
                {
                    "name": "asd",
                    "type": "stdio",
                    "command": "uv",
                    "args": ["run", "asd-mcp"],
                    "permissions": ["asd.*"],
                },
                {
                    "name": "ocd",
                    "type": "stdio",
                    "command": "uv",
                    "args": ["run", "ocd-mcp"],
                    "permissions": ["ocd.*"],
                },
            ]
        }
        path = tmp_path / "mcp.json"
        path.write_text(json.dumps(data))
        reg = MCPRegistry(path)
        assert len(reg) == 3
        assert sorted(reg.list_servers()) == ["adhd", "asd", "ocd"]

    def test_each_server_has_permissions(self, tmp_path: Path):
        data = {
            "servers": [
                {
                    "name": "adhd",
                    "command": "uv",
                    "args": ["run", "adhd-mcp"],
                    "permissions": ["adhd.*"],
                },
                {
                    "name": "asd",
                    "command": "uv",
                    "args": ["run", "asd-mcp"],
                    "permissions": ["asd.*"],
                },
                {
                    "name": "ocd",
                    "command": "uv",
                    "args": ["run", "ocd-mcp"],
                    "permissions": ["ocd.*"],
                },
            ]
        }
        path = tmp_path / "mcp.json"
        path.write_text(json.dumps(data))
        reg = MCPRegistry(path)
        for name in ["adhd", "asd", "ocd"]:
            config = reg.get(name)
            assert config is not None
            assert len(config.permissions) > 0

    def test_resolve_path_discovers_project_config(self, tmp_path: Path, monkeypatch):
        """_resolve_path should find .brainxio/mcp.json in the project dir."""
        from another_intelligence.mcp.client import MCPRegistry as Reg

        brainxio_dir = tmp_path / ".brainxio"
        brainxio_dir.mkdir()
        config_path = brainxio_dir / "mcp.json"
        config_path.write_text(
            json.dumps(
                {
                    "servers": [
                        {
                            "name": "adhd",
                            "command": "uv",
                            "args": ["run", "adhd-mcp"],
                            "permissions": ["adhd.*"],
                        }
                    ]
                }
            )
        )

        monkeypatch.chdir(tmp_path)
        resolved = Reg._resolve_path(None)
        assert resolved is not None
        assert resolved.parent.name == ".brainxio"


class TestMCPServerConfig:
    """Pydantic validation for server configuration."""

    def test_minimal_config(self):
        cfg = MCPServerConfig(name="test", command="echo")
        assert cfg.name == "test"
        assert cfg.command == "echo"
        assert cfg.type == "stdio"
        assert cfg.args == []
        assert cfg.permissions == []

    def test_full_config(self):
        cfg = MCPServerConfig(
            name="fs",
            type="stdio",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
            permissions=["filesystem.read", "filesystem.write"],
            env={"NODE_ENV": "production"},
            timeout=10.0,
        )
        assert cfg.timeout == 10.0
        assert cfg.env == {"NODE_ENV": "production"}


class TestMCPRegistry:
    """Configuration loading and server registry."""

    def test_empty_registry(self, tmp_path: Path):
        reg = MCPRegistry(tmp_path / "nonexistent.json")
        assert reg.list_servers() == []
        assert len(reg) == 0
        assert "fs" not in reg

    def test_load_from_path(self, tmp_path: Path):
        data = {
            "servers": [
                {"name": "fs", "command": "npx", "args": ["server-filesystem"]},
                {"name": "git", "command": "python", "args": ["-m", "git_server"]},
                {"name": "browser", "command": "npx", "args": ["server-puppeteer"]},
            ]
        }
        path = tmp_path / "mcp.json"
        path.write_text(json.dumps(data))
        reg = MCPRegistry(path)
        assert len(reg) == 3
        assert sorted(reg.list_servers()) == ["browser", "fs", "git"]
        assert "fs" in reg
        assert reg.get("fs").command == "npx"
        assert reg.get("missing") is None

    def test_missing_file_is_empty(self, tmp_path: Path):
        reg = MCPRegistry(tmp_path / "nonexistent.json")
        assert len(reg) == 0

    def test_invalid_json_ignored(self, tmp_path: Path):
        path = tmp_path / "mcp.json"
        path.write_text("not json")
        with pytest.raises(json.JSONDecodeError):
            MCPRegistry(path)


class MockConnection(MCPConnection):
    """In-memory mock connection for testing."""

    def __init__(self, config: MCPServerConfig, tools: list[dict[str, Any]] | None = None) -> None:
        super().__init__(config)
        self._tools = tools or []
        self.call_log: list[dict[str, Any]] = []

    async def connect(self) -> None:
        self._connected = True

    async def disconnect(self) -> None:
        self._connected = False

    async def send_request(self, method: str, params: dict[str, Any] | None = None) -> Any:
        if method == "tools/list":
            return {"tools": self._tools}
        if method == "tools/call":
            self.call_log.append({"method": method, "params": params})
            return {"content": [{"type": "text", "text": "mock-result"}]}
        return None


class TestMCPClientInit:
    """Construction and default state."""

    def test_empty_client(self):
        reg = MCPRegistry()
        perms = PermissionEngine()
        client = MCPClient(reg, perms)
        assert client._registry is reg
        assert client._permissions is perms

    def test_register_hook(self):
        reg = MCPRegistry()
        client = MCPClient(reg, PermissionEngine())
        mock_hook = MagicMock()
        client.register_hook("PreToolUse", mock_hook)
        assert "PreToolUse" in client._hooks


class TestMCPClientToolListing:
    """Tool discovery and caching."""

    def test_list_tools_uses_mock_connection(self, tmp_path: Path):
        data = {
            "servers": [
                {
                    "name": "fs",
                    "command": "echo",
                    "args": ["fs"],
                }
            ]
        }
        path = tmp_path / "mcp.json"
        path.write_text(json.dumps(data))
        reg = MCPRegistry(path)
        client = MCPClient(reg, PermissionEngine())

        # Inject mock connection
        mock_conn = MockConnection(
            reg.get("fs"),
            tools=[{"name": "read", "description": "Read a file"}],
        )
        client._connections["fs"] = mock_conn

        tools = asyncio.run(client.list_tools("fs"))
        assert "fs" in tools
        assert len(tools["fs"]) == 1
        assert tools["fs"][0].name == "read"
        # Cached on second call
        tools2 = asyncio.run(client.list_tools("fs"))
        assert tools2 == tools

    def test_list_tools_all_servers(self, tmp_path: Path):
        data = {
            "servers": [
                {"name": "a", "command": "echo"},
                {"name": "b", "command": "echo"},
            ]
        }
        path = tmp_path / "mcp.json"
        path.write_text(json.dumps(data))
        reg = MCPRegistry(path)
        client = MCPClient(reg, PermissionEngine())
        client._connections["a"] = MockConnection(reg.get("a"), tools=[{"name": "t1"}])
        client._connections["b"] = MockConnection(reg.get("b"), tools=[{"name": "t2"}])

        tools = asyncio.run(client.list_tools())
        assert len(tools) == 2
        assert tools["a"][0].name == "t1"
        assert tools["b"][0].name == "t2"

    def test_clear_cache(self, tmp_path: Path):
        data = {"servers": [{"name": "fs", "command": "echo"}]}
        path = tmp_path / "mcp.json"
        path.write_text(json.dumps(data))
        reg = MCPRegistry(path)
        client = MCPClient(reg, PermissionEngine())
        client._connections["fs"] = MockConnection(reg.get("fs"), tools=[{"name": "read"}])
        asyncio.run(client.list_tools("fs"))
        assert "fs" in client._tools_cache
        client.clear_cache()
        assert "fs" not in client._tools_cache


class TestMCPClientCallTool:
    """Tool execution with permissions and hooks."""

    def test_call_tool_success_with_allow(self, tmp_path: Path):
        data = {"servers": [{"name": "fs", "command": "echo"}]}
        path = tmp_path / "mcp.json"
        path.write_text(json.dumps(data))
        reg = MCPRegistry(path)
        config = PermissionConfig(grants=[Grant(capability="mcp.fs.read", allowed_by="test")])
        perms = PermissionEngine()
        perms._config = config
        client = MCPClient(reg, perms)
        client._connections["fs"] = MockConnection(reg.get("fs"), tools=[{"name": "read"}])

        result = asyncio.run(client.call_tool("fs", "read", {"path": "/tmp"}))
        assert result["success"] is True
        assert result["error"] is None

    def test_call_tool_denied_without_grant(self, tmp_path: Path):
        data = {"servers": [{"name": "fs", "command": "echo"}]}
        path = tmp_path / "mcp.json"
        path.write_text(json.dumps(data))
        reg = MCPRegistry(path)
        client = MCPClient(reg, PermissionEngine())
        client._connections["fs"] = MockConnection(reg.get("fs"))

        result = asyncio.run(client.call_tool("fs", "read", {"path": "/tmp"}))
        assert result["success"] is False
        assert "Permission denied" in result["error"]
        assert result["decision"] == "deny"

    def test_call_tool_unknown_server_raises(self):
        client = MCPClient(MCPRegistry(), PermissionEngine())
        with pytest.raises(ValueError, match="Unknown MCP server"):
            asyncio.run(client.call_tool("missing", "tool"))

    def test_call_tool_with_ask_decision(self, tmp_path: Path):
        data = {"servers": [{"name": "fs", "command": "echo"}]}
        path = tmp_path / "mcp.json"
        path.write_text(json.dumps(data))
        reg = MCPRegistry(path)
        config = PermissionConfig(
            grants=[Grant(capability="mcp.fs.write", require_confirmation=True)]
        )
        perms = PermissionEngine()
        perms._config = config
        client = MCPClient(reg, perms)
        client._connections["fs"] = MockConnection(reg.get("fs"))

        result = asyncio.run(client.call_tool("fs", "write", {"path": "/tmp"}))
        assert result["success"] is False
        assert result["decision"] == "ask"


class TestMCPClientEvents:
    """Event emission during tool calls."""

    def test_pre_tool_use_emitted(self, tmp_path: Path):
        data = {"servers": [{"name": "fs", "command": "echo"}]}
        path = tmp_path / "mcp.json"
        path.write_text(json.dumps(data))
        reg = MCPRegistry(path)
        config = PermissionConfig(grants=[Grant(capability="mcp.fs.read")])
        perms = PermissionEngine()
        perms._config = config
        client = MCPClient(reg, perms)
        client._connections["fs"] = MockConnection(reg.get("fs"))

        events: list[Any] = []
        client.register_hook("PreToolUse", events.append)
        asyncio.run(client.call_tool("fs", "read"))
        assert any(isinstance(e, PreToolUse) for e in events)
        pre = [e for e in events if isinstance(e, PreToolUse)][0]
        assert pre.tool_name == "fs.read"

    def test_post_tool_use_emitted(self, tmp_path: Path):
        data = {"servers": [{"name": "fs", "command": "echo"}]}
        path = tmp_path / "mcp.json"
        path.write_text(json.dumps(data))
        reg = MCPRegistry(path)
        config = PermissionConfig(grants=[Grant(capability="mcp.fs.read")])
        perms = PermissionEngine()
        perms._config = config
        client = MCPClient(reg, perms)
        client._connections["fs"] = MockConnection(reg.get("fs"))

        events: list[Any] = []
        client.register_hook("PostToolUse", events.append)
        asyncio.run(client.call_tool("fs", "read"))
        assert any(isinstance(e, PostToolUse) for e in events)
        post = [e for e in events if isinstance(e, PostToolUse)][0]
        assert post.tool_name == "fs.read"
        assert post.success is True
        assert post.duration_ms >= 0.0

    def test_mcp_tool_called_emitted(self, tmp_path: Path):
        data = {"servers": [{"name": "fs", "command": "echo"}]}
        path = tmp_path / "mcp.json"
        path.write_text(json.dumps(data))
        reg = MCPRegistry(path)
        config = PermissionConfig(grants=[Grant(capability="mcp.fs.read")])
        perms = PermissionEngine()
        perms._config = config
        client = MCPClient(reg, perms)
        client._connections["fs"] = MockConnection(reg.get("fs"))

        events: list[Any] = []
        client.register_hook("MCPToolCalled", events.append)
        asyncio.run(client.call_tool("fs", "read", {"path": "/"}))
        assert any(isinstance(e, MCPToolCalled) for e in events)
        mcp = [e for e in events if isinstance(e, MCPToolCalled)][0]
        assert mcp.server == "fs"
        assert mcp.tool == "read"
        assert mcp.params.get("path") == "/"

    def test_events_on_permission_denied(self, tmp_path: Path):
        data = {"servers": [{"name": "fs", "command": "echo"}]}
        path = tmp_path / "mcp.json"
        path.write_text(json.dumps(data))
        reg = MCPRegistry(path)
        client = MCPClient(reg, PermissionEngine())
        client._connections["fs"] = MockConnection(reg.get("fs"))

        events: list[Any] = []
        client.register_hook("PostToolUse", events.append)
        client.register_hook("MCPToolCalled", events.append)
        asyncio.run(client.call_tool("fs", "read"))
        assert any(isinstance(e, PostToolUse) and e.success is False for e in events)
        assert any(isinstance(e, MCPToolCalled) for e in events)

    def test_hook_exception_ignored(self, tmp_path: Path):
        data = {"servers": [{"name": "fs", "command": "echo"}]}
        path = tmp_path / "mcp.json"
        path.write_text(json.dumps(data))
        reg = MCPRegistry(path)
        config = PermissionConfig(grants=[Grant(capability="mcp.fs.read")])
        perms = PermissionEngine()
        perms._config = config
        client = MCPClient(reg, perms)
        client._connections["fs"] = MockConnection(reg.get("fs"))

        def bad_hook(event: Any) -> None:
            raise RuntimeError("boom")

        client.register_hook("PreToolUse", bad_hook)
        # Should not raise
        result = asyncio.run(client.call_tool("fs", "read"))
        assert result["success"] is True


class TestMCPClientPermissionsPipeline:
    """Full Permissions + Hook pipeline integration."""

    def test_permission_check_uses_correct_capability(self, tmp_path: Path):
        data = {"servers": [{"name": "git", "command": "echo"}]}
        path = tmp_path / "mcp.json"
        path.write_text(json.dumps(data))
        reg = MCPRegistry(path)
        config = PermissionConfig(
            grants=[
                Grant(capability="mcp.git.read"),
                Grant(capability="mcp.fs.read"),
            ]
        )
        perms = PermissionEngine()
        perms._config = config
        client = MCPClient(reg, perms)
        client._connections["git"] = MockConnection(reg.get("git"))

        result = asyncio.run(client.call_tool("git", "read"))
        assert result["success"] is True

    def test_deny_rule_blocks_tool(self, tmp_path: Path):
        data = {"servers": [{"name": "fs", "command": "echo"}]}
        path = tmp_path / "mcp.json"
        path.write_text(json.dumps(data))
        reg = MCPRegistry(path)
        config = PermissionConfig(
            grants=[Grant(capability="mcp.fs.*")],
            deny_rules=["mcp.fs.delete"],
        )
        perms = PermissionEngine()
        perms._config = config
        client = MCPClient(reg, perms)
        client._connections["fs"] = MockConnection(reg.get("fs"))

        result = asyncio.run(client.call_tool("fs", "delete", {"path": "/"}))
        assert result["success"] is False
        assert "deny" in result["error"].lower()

    def test_wildcard_grant_allows_multiple_tools(self, tmp_path: Path):
        data = {"servers": [{"name": "fs", "command": "echo"}]}
        path = tmp_path / "mcp.json"
        path.write_text(json.dumps(data))
        reg = MCPRegistry(path)
        config = PermissionConfig(grants=[Grant(capability="mcp.fs.*")])
        perms = PermissionEngine()
        perms._config = config
        client = MCPClient(reg, perms)
        client._connections["fs"] = MockConnection(
            reg.get("fs"),
            tools=[{"name": "read"}, {"name": "write"}, {"name": "list"}],
        )

        for tool in ["read", "write", "list"]:
            result = asyncio.run(client.call_tool("fs", tool))
            assert result["success"] is True, f"{tool} should be allowed"

    def test_audit_log_records_mcp_decisions(self, tmp_path: Path):
        data = {"servers": [{"name": "fs", "command": "echo"}]}
        path = tmp_path / "mcp.json"
        path.write_text(json.dumps(data))
        reg = MCPRegistry(path)
        perms = PermissionEngine()
        client = MCPClient(reg, perms)
        client._connections["fs"] = MockConnection(reg.get("fs"))

        asyncio.run(client.call_tool("fs", "read"))
        log = perms.get_audit_log()
        assert len(log) >= 1
        assert log[-1].capability == "mcp.fs.read"
        assert log[-1].decision == "deny"


class TestMCPClientConnectionManagement:
    """Connection lifecycle."""

    def test_connect_all(self, tmp_path: Path):
        data = {
            "servers": [
                {"name": "a", "command": "echo"},
                {"name": "b", "command": "echo"},
            ]
        }
        path = tmp_path / "mcp.json"
        path.write_text(json.dumps(data))
        reg = MCPRegistry(path)
        client = MCPClient(reg, PermissionEngine())
        client._connections["a"] = MockConnection(reg.get("a"))
        client._connections["b"] = MockConnection(reg.get("b"))

        connected = asyncio.run(client.connect_all())
        assert sorted(connected) == ["a", "b"]
        assert client._connections["a"].connected
        assert client._connections["b"].connected

    def test_disconnect_all(self, tmp_path: Path):
        data = {"servers": [{"name": "a", "command": "echo"}]}
        path = tmp_path / "mcp.json"
        path.write_text(json.dumps(data))
        reg = MCPRegistry(path)
        client = MCPClient(reg, PermissionEngine())
        conn = MockConnection(reg.get("a"))
        client._connections["a"] = conn
        asyncio.run(client.connect_all())
        assert client._connections["a"].connected
        asyncio.run(client.disconnect_all())
        assert not conn.connected
        assert "a" not in client._connections


# asyncio is imported at the top of the file
