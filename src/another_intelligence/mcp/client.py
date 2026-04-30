"""MCP client with auto-discovery, tool caching, and permissions integration."""

from __future__ import annotations

import asyncio
import contextlib
import json
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from another_intelligence.events import MCPToolCalled, PostToolUse, PreToolUse
from another_intelligence.permissions.engine import PermissionEngine


class MCPServerHealth(BaseModel):
    """Health status for a single MCP server."""

    name: str
    connected: bool
    healthy: bool = False
    version: str | None = None
    tool_count: int = 0
    last_checked: datetime | None = None
    error: str | None = None


class MCPToolDefinition(BaseModel):
    """Definition of a tool exposed by an MCP server."""

    name: str
    description: str | None = None
    input_schema: dict[str, Any] = Field(default_factory=dict)


class MCPServerConfig(BaseModel):
    """Configuration for a single MCP server."""

    name: str
    type: str = "stdio"
    command: str
    args: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    env: dict[str, str] | None = None
    timeout: float = 30.0


class MCPRegistry:
    """Loads and manages MCP server configurations from mcp.json."""

    def __init__(self, config_path: Path | str | None = None) -> None:
        self._servers: dict[str, MCPServerConfig] = {}
        self._config_path = self._resolve_path(config_path)
        self._load()

    @staticmethod
    def _resolve_path(config_path: Path | str | None) -> Path | None:
        if config_path is not None:
            return Path(config_path)
        # Search global then project config
        global_path = Path.home() / ".brainxio" / "mcp.json"
        if global_path.exists():
            return global_path
        project_path = Path(".brainxio") / "mcp.json"
        if project_path.exists():
            return project_path
        return None

    def _load(self) -> None:
        if self._config_path is None or not self._config_path.exists():
            return
        with self._config_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        for server_data in data.get("servers", []):
            config = MCPServerConfig(**server_data)
            self._servers[config.name] = config

    def get(self, name: str) -> MCPServerConfig | None:
        return self._servers.get(name)

    def list_servers(self) -> list[str]:
        return list(self._servers.keys())

    def __len__(self) -> int:
        return len(self._servers)

    def __contains__(self, name: str) -> bool:
        return name in self._servers


class MCPConnection(ABC):
    """Abstract connection to an MCP server."""

    def __init__(self, config: MCPServerConfig) -> None:
        self._config = config
        self._connected = False

    @property
    def config(self) -> MCPServerConfig:
        return self._config

    @property
    def connected(self) -> bool:
        return self._connected

    @abstractmethod
    async def connect(self) -> None:
        """Establish the connection."""

    @abstractmethod
    async def disconnect(self) -> None:
        """Close the connection."""

    @abstractmethod
    async def send_request(self, method: str, params: dict[str, Any] | None = None) -> Any:
        """Send a JSON-RPC request and return the result."""

    async def list_tools(self) -> list[MCPToolDefinition]:
        """Fetch tool definitions from the server."""
        raw = await self.send_request("tools/list")
        tools = raw.get("tools", []) if isinstance(raw, dict) else []
        return [MCPToolDefinition(**t) for t in tools]

    async def call_tool(self, name: str, params: dict[str, Any] | None = None) -> Any:
        """Execute a tool on the server."""
        return await self.send_request("tools/call", {"name": name, "arguments": params or {}})


class _JsonRpcState:
    """Shared JSON-RPC request state for stdio transport."""

    _counter: int = 0
    _pending: dict[int, asyncio.Future[Any]] = {}
    _lock: asyncio.Lock = asyncio.Lock()

    @classmethod
    async def next_id(cls) -> int:
        async with cls._lock:
            cls._counter += 1
            return cls._counter

    @classmethod
    def register_future(cls, req_id: int, future: asyncio.Future[Any]) -> None:
        cls._pending[req_id] = future

    @classmethod
    def resolve(cls, req_id: int, result: Any) -> bool:
        future = cls._pending.pop(req_id, None)
        if future is not None and not future.done():
            future.set_result(result)
            return True
        return False

    @classmethod
    def reject(cls, req_id: int, error: Exception) -> bool:
        future = cls._pending.pop(req_id, None)
        if future is not None and not future.done():
            future.set_exception(error)
            return True
        return False


class StdioConnection(MCPConnection):
    """JSON-RPC connection over stdio via asyncio subprocess."""

    def __init__(self, config: MCPServerConfig) -> None:
        super().__init__(config)
        self._proc: asyncio.subprocess.Process | None = None
        self._reader_task: asyncio.Task[None] | None = None
        self._write_lock = asyncio.Lock()

    async def connect(self) -> None:
        import os

        env = {**dict(os.environ), **(self._config.env or {})}
        self._proc = await asyncio.create_subprocess_exec(
            self._config.command,
            *self._config.args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        self._connected = True
        self._reader_task = asyncio.create_task(self._read_loop())
        await asyncio.sleep(0)  # yield so the reader task can start on single-core
        # Initialize session per MCP spec
        await self.send_request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "another-intelligence", "version": "0.1.0"},
            },
        )
        await self.send_notification("notifications/initialized")

    async def disconnect(self) -> None:
        self._connected = False
        if self._reader_task is not None:
            self._reader_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._reader_task
        if self._proc is not None and self._proc.returncode is None:
            self._proc.terminate()
            try:
                await asyncio.wait_for(self._proc.wait(), timeout=2.0)
            except TimeoutError:
                self._proc.kill()
                await self._proc.wait()
        self._proc = None
        self._reader_task = None

    async def _read_loop(self) -> None:
        if self._proc is None or self._proc.stdout is None:
            return
        try:
            while self._connected:
                line = await self._proc.stdout.readline()
                if not line:
                    break
                try:
                    msg = json.loads(line.decode("utf-8").strip())
                except (json.JSONDecodeError, UnicodeDecodeError):
                    continue
                if msg.get("jsonrpc") != "2.0":
                    continue
                req_id = msg.get("id")
                if req_id is None:
                    continue
                if "error" in msg:
                    error = msg["error"]
                    _JsonRpcState.reject(
                        req_id,
                        RuntimeError(f"JSON-RPC error {error.get('code')}: {error.get('message')}"),
                    )
                else:
                    _JsonRpcState.resolve(req_id, msg.get("result"))
        except asyncio.CancelledError:
            raise

    async def send_request(self, method: str, params: dict[str, Any] | None = None) -> Any:
        if not self._connected or self._proc is None or self._proc.stdin is None:
            raise RuntimeError("Connection not established")

        req_id = await _JsonRpcState.next_id()
        request: dict[str, Any] = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
        }
        if params is not None:
            request["params"] = params

        loop = asyncio.get_event_loop()
        future: asyncio.Future[Any] = loop.create_future()
        _JsonRpcState.register_future(req_id, future)

        payload = json.dumps(request) + "\n"
        async with self._write_lock:
            self._proc.stdin.write(payload.encode("utf-8"))
            await self._proc.stdin.drain()

        try:
            return await asyncio.wait_for(future, timeout=self._config.timeout)
        except TimeoutError:
            _JsonRpcState.reject(req_id, TimeoutError(f"Request {method} timed out"))
            raise

    async def send_notification(self, method: str, params: dict[str, Any] | None = None) -> None:
        """Send a JSON-RPC notification (no response expected)."""
        if not self._connected or self._proc is None or self._proc.stdin is None:
            raise RuntimeError("Connection not established")

        request: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            request["params"] = params

        payload = json.dumps(request) + "\n"
        async with self._write_lock:
            self._proc.stdin.write(payload.encode("utf-8"))
            await self._proc.stdin.drain()


class MCPClient:
    """MCP client integrating with permissions, hooks, and the event bus."""

    def __init__(
        self,
        registry: MCPRegistry,
        permission_engine: PermissionEngine,
    ) -> None:
        self._registry = registry
        self._permissions = permission_engine
        self._tools_cache: dict[str, list[MCPToolDefinition]] = {}
        self._hooks: dict[str, list[Callable[[Any], None]]] = {}
        self._connections: dict[str, MCPConnection] = {}

    def register_hook(self, event_type: str, callback: Callable[[Any], None]) -> None:
        self._hooks.setdefault(event_type, []).append(callback)

    def _emit(self, event: Any) -> None:
        for callback in self._hooks.get(type(event).__name__, []):
            try:
                callback(event)
            except Exception:
                continue

    def _get_connection(self, server_name: str) -> MCPConnection:
        if server_name not in self._connections:
            config = self._registry.get(server_name)
            if config is None:
                raise ValueError(f"Unknown MCP server: {server_name}")
            if config.type == "stdio":
                self._connections[server_name] = StdioConnection(config)
            else:
                raise ValueError(f"Unsupported transport type: {config.type}")
        return self._connections[server_name]

    async def connect_all(self) -> list[str]:
        """Connect to all configured servers and return connected names."""
        connected: list[str] = []
        for name in self._registry.list_servers():
            try:
                conn = self._get_connection(name)
                if not conn.connected:
                    await conn.connect()
                connected.append(name)
            except Exception:
                continue
        return connected

    async def disconnect_all(self) -> None:
        """Disconnect from all servers."""
        for conn in self._connections.values():
            if conn.connected:
                await conn.disconnect()
        self._connections.clear()

    async def list_tools(
        self, server_name: str | None = None
    ) -> dict[str, list[MCPToolDefinition]]:
        """List tools from a specific server or all servers."""
        servers = [server_name] if server_name is not None else self._registry.list_servers()

        result: dict[str, list[MCPToolDefinition]] = {}
        for name in servers:
            if name in self._tools_cache:
                result[name] = self._tools_cache[name]
                continue
            conn = self._get_connection(name)
            if not conn.connected:
                await conn.connect()
            tools = await conn.list_tools()
            self._tools_cache[name] = tools
            result[name] = tools
        return result

    def _build_capability(self, server_name: str, tool_name: str) -> str:
        return f"mcp.{server_name}.{tool_name}"

    async def call_tool(
        self,
        server_name: str,
        tool_name: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute an MCP tool with full permissions + hook pipeline.

        Flow:
            1. Validate server exists.
            2. Emit PreToolUse.
            3. Check permissions.
            4. Execute tool.
            5. Emit PostToolUse + MCPToolCalled.
        """
        params = params or {}
        capability = self._build_capability(server_name, tool_name)

        # 1. Validate
        if server_name not in self._registry:
            raise ValueError(f"Unknown MCP server: {server_name}")

        # 2. PreToolUse hook
        pre_event = PreToolUse(tool_name=f"{server_name}.{tool_name}", arguments=params)
        self._emit(pre_event)

        # 3. Permissions check
        decision = self._permissions.check(
            capability, context={"server": server_name, "tool": tool_name, "params": params}
        )
        if not decision.allowed:
            duration_ms = 0.0
            post_event = PostToolUse(
                tool_name=f"{server_name}.{tool_name}",
                success=False,
                duration_ms=duration_ms,
            )
            self._emit(post_event)
            self._emit(
                MCPToolCalled(
                    server=server_name,
                    tool=tool_name,
                    params={"error": decision.reason, **params},
                )
            )
            return {
                "success": False,
                "error": f"Permission denied: {decision.reason}",
                "decision": decision.decision,
            }

        # 4. Execute
        start = time.perf_counter()
        try:
            conn = self._get_connection(server_name)
            if not conn.connected:
                await conn.connect()
            result = await conn.call_tool(tool_name, params)
            success = True
            error: str | None = None
        except Exception as exc:
            success = False
            result = None
            error = str(exc)
        duration_ms = (time.perf_counter() - start) * 1000

        # 5. PostToolUse + MCPToolCalled
        post_event = PostToolUse(
            tool_name=f"{server_name}.{tool_name}",
            success=success,
            duration_ms=duration_ms,
        )
        self._emit(post_event)
        self._emit(
            MCPToolCalled(
                server=server_name,
                tool=tool_name,
                params={"result": result, "error": error, **params},
            )
        )

        return {
            "success": success,
            "result": result,
            "error": error,
            "duration_ms": duration_ms,
        }

    def clear_cache(self) -> None:
        """Clear the tool definitions cache."""
        self._tools_cache.clear()

    async def health_check(self, server_name: str | None = None) -> dict[str, MCPServerHealth]:
        """Check health of one or all configured MCP servers."""
        servers = [server_name] if server_name is not None else self._registry.list_servers()
        result: dict[str, MCPServerHealth] = {}

        for name in servers:
            config = self._registry.get(name)
            if config is None:
                result[name] = MCPServerHealth(
                    name=name,
                    connected=False,
                    error="Not configured",
                )
                continue

            try:
                conn = self._get_connection(name)
                if not conn.connected:
                    await conn.connect()
                tools = await conn.list_tools()
                result[name] = MCPServerHealth(
                    name=name,
                    connected=True,
                    healthy=True,
                    version="2024-11-05",
                    tool_count=len(tools),
                    last_checked=datetime.now(UTC),
                )
            except Exception as exc:
                result[name] = MCPServerHealth(
                    name=name,
                    connected=getattr(self._connections.get(name), "connected", False),
                    healthy=False,
                    error=str(exc),
                    last_checked=datetime.now(UTC),
                )

        return result

    async def call_tool_with_retry(
        self,
        server_name: str,
        tool_name: str,
        params: dict[str, Any] | None = None,
        max_retries: int = 3,
        base_delay: float = 0.5,
    ) -> dict[str, Any]:
        """Execute a tool with exponential backoff on transient failures.

        Args:
            server_name: MCP server name.
            tool_name: Tool to invoke.
            params: Tool parameters.
            max_retries: Maximum retry attempts.
            base_delay: Initial delay in seconds (doubles each retry).

        Returns:
            Result dict with ``success``, ``result``, and ``retries`` keys.
        """
        last_error: str | None = None
        for attempt in range(max_retries):
            try:
                result = await self.call_tool(server_name, tool_name, params)
                if result.get("success"):
                    result["retries"] = attempt
                    return result
                last_error = result.get("error", "Unknown error")
            except Exception as exc:
                last_error = str(exc)

            if attempt < max_retries - 1:
                delay = base_delay * (2**attempt)
                await asyncio.sleep(delay)

        return {
            "success": False,
            "result": None,
            "error": last_error,
            "retries": max_retries,
        }

    def get_server_status(
        self,
        server_name: str | None = None,
    ) -> dict[str, dict[str, Any]]:
        """Return configuration and connection status for servers.

        This is a synchronous summary useful for CLI reporting.
        """
        servers = [server_name] if server_name is not None else self._registry.list_servers()
        result: dict[str, dict[str, Any]] = {}

        for name in servers:
            config = self._registry.get(name)
            conn = self._connections.get(name)
            result[name] = {
                "configured": config is not None,
                "transport": config.type if config else "unknown",
                "command": config.command if config else "?",
                "connected": conn.connected if conn else False,
                "tools_cached": len(self._tools_cache.get(name, [])),
            }

        return result
