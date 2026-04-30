"""Integration tests for MCP stdio transport against real servers.

These tests require Node.js and npx to be available on PATH.
They are skipped automatically if the runtime is missing.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from another_intelligence.events import MCPToolCalled, PreToolUse
from another_intelligence.mcp.client import MCPClient, MCPRegistry, StdioConnection
from another_intelligence.permissions.engine import (
    Grant,
    PermissionConfig,
    PermissionEngine,
)


@pytest.fixture
def node_available() -> bool:
    """Check if Node.js and npx are available."""
    import shutil

    return shutil.which("npx") is not None and shutil.which("node") is not None


@pytest.fixture
def fs_server_config(tmp_path: Path) -> dict[str, Any]:
    """Create a temporary MCP config pointing to the filesystem server."""
    serve_dir = tmp_path / "serve"
    serve_dir.mkdir()
    (serve_dir / "hello.txt").write_text("hello from mcp fs")
    return {
        "servers": [
            {
                "name": "fs",
                "type": "stdio",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", str(serve_dir)],
                "permissions": ["filesystem.read"],
                "timeout": 120.0,
            }
        ]
    }


@pytest.fixture
def fs_registry(fs_server_config: dict[str, Any], tmp_path: Path) -> MCPRegistry:
    """Registry loaded from temporary config."""
    path = tmp_path / "mcp.json"
    path.write_text(json.dumps(fs_server_config))
    return MCPRegistry(path)


@pytest.fixture
def permissive_engine(tmp_path: Path) -> PermissionEngine:
    """Engine that allows all MCP filesystem operations."""
    config = PermissionConfig(grants=[Grant(capability="mcp.fs.*", allowed_by="test")])
    path = tmp_path / "permissions.json"
    path.write_text(json.dumps({"permissions": config.model_dump()}))
    return PermissionEngine(path)


@pytest.fixture
def deny_engine(tmp_path: Path) -> PermissionEngine:
    """Engine that denies all operations by default."""
    path = tmp_path / "permissions.json"
    path.write_text(json.dumps({"permissions": {"grants": []}}))
    return PermissionEngine(path)


@pytest.mark.asyncio
class TestStdioConnection:
    """Direct stdio transport tests."""

    async def test_connect_and_list_tools(
        self,
        node_available: bool,
        fs_registry: MCPRegistry,
    ) -> None:
        if not node_available:
            pytest.skip("Node.js / npx not available")

        config = fs_registry.get("fs")
        assert config is not None
        conn = StdioConnection(config)
        await conn.connect()
        assert conn.connected

        tools = await conn.list_tools()
        assert len(tools) > 0
        names = [t.name for t in tools]
        assert "read_file" in names

        await conn.disconnect()
        assert not conn.connected

    async def test_read_file(
        self,
        node_available: bool,
        fs_registry: MCPRegistry,
        fs_server_config: dict[str, Any],
    ) -> None:
        if not node_available:
            pytest.skip("Node.js / npx not available")

        serve_dir = Path(fs_server_config["servers"][0]["args"][-1])
        config = fs_registry.get("fs")
        conn = StdioConnection(config)
        await conn.connect()

        result = await conn.call_tool("read_file", {"path": str(serve_dir / "hello.txt")})
        assert isinstance(result, dict)
        content = result.get("content", [])
        texts = [c["text"] for c in content if c.get("type") == "text"]
        assert any("hello from mcp fs" in t for t in texts)

        await conn.disconnect()


@pytest.mark.asyncio
class TestMCPClientIntegration:
    """End-to-end MCPClient tests with real subprocess."""

    async def test_connect_all(
        self,
        node_available: bool,
        fs_registry: MCPRegistry,
        permissive_engine: PermissionEngine,
    ) -> None:
        if not node_available:
            pytest.skip("Node.js / npx not available")

        client = MCPClient(fs_registry, permissive_engine)
        connected = await client.connect_all()
        assert connected == ["fs"]
        await client.disconnect_all()

    async def test_list_tools_via_client(
        self,
        node_available: bool,
        fs_registry: MCPRegistry,
        permissive_engine: PermissionEngine,
    ) -> None:
        if not node_available:
            pytest.skip("Node.js / npx not available")

        client = MCPClient(fs_registry, permissive_engine)
        tools = await client.list_tools("fs")
        assert "fs" in tools
        names = [t.name for t in tools["fs"]]
        assert "read_file" in names
        await client.disconnect_all()

    async def test_call_tool_with_permissions(
        self,
        node_available: bool,
        fs_registry: MCPRegistry,
        permissive_engine: PermissionEngine,
        fs_server_config: dict[str, Any],
    ) -> None:
        if not node_available:
            pytest.skip("Node.js / npx not available")

        serve_dir = Path(fs_server_config["servers"][0]["args"][-1])
        client = MCPClient(fs_registry, permissive_engine)

        result = await client.call_tool(
            "fs",
            "read_file",
            {"path": str(serve_dir / "hello.txt")},
        )
        assert result["success"] is True
        assert result["error"] is None
        await client.disconnect_all()

    async def test_call_tool_denied(
        self,
        node_available: bool,
        fs_registry: MCPRegistry,
        deny_engine: PermissionEngine,
    ) -> None:
        if not node_available:
            pytest.skip("Node.js / npx not available")

        client = MCPClient(fs_registry, deny_engine)
        result = await client.call_tool("fs", "read_file", {"path": "/etc/passwd"})
        assert result["success"] is False
        assert "Permission denied" in result["error"]
        await client.disconnect_all()

    async def test_hooks_fire(
        self,
        node_available: bool,
        fs_registry: MCPRegistry,
        permissive_engine: PermissionEngine,
        fs_server_config: dict[str, Any],
    ) -> None:
        if not node_available:
            pytest.skip("Node.js / npx not available")

        serve_dir = Path(fs_server_config["servers"][0]["args"][-1])
        client = MCPClient(fs_registry, permissive_engine)

        events: list[Any] = []
        client.register_hook("PreToolUse", lambda e: events.append(("pre", e)))
        client.register_hook("PostToolUse", lambda e: events.append(("post", e)))
        client.register_hook("MCPToolCalled", lambda e: events.append(("mcp", e)))

        await client.call_tool("fs", "read_file", {"path": str(serve_dir / "hello.txt")})

        types = [t for t, _ in events]
        assert "pre" in types
        assert "post" in types
        assert "mcp" in types

        pre = [e for t, e in events if t == "pre"][0]
        assert isinstance(pre, PreToolUse)
        assert pre.tool_name == "fs.read_file"

        mcp = [e for t, e in events if t == "mcp"][0]
        assert isinstance(mcp, MCPToolCalled)
        assert mcp.server == "fs"
        assert mcp.tool == "read_file"

        await client.disconnect_all()

    async def test_tool_cache(
        self,
        node_available: bool,
        fs_registry: MCPRegistry,
        permissive_engine: PermissionEngine,
    ) -> None:
        if not node_available:
            pytest.skip("Node.js / npx not available")

        client = MCPClient(fs_registry, permissive_engine)

        # First call hits the server
        tools1 = await client.list_tools("fs")
        assert "fs" in tools1

        # Second call uses cache (no new connection needed)
        tools2 = await client.list_tools("fs")
        assert tools2 == tools1

        client.clear_cache()
        assert not client._tools_cache

        await client.disconnect_all()
