---
title: MCP Integration Testing
tags: [reference, testing]
updated: '2026-05-01'
---

# MCP Integration Testing

## Overview

The MCP (Model Context Protocol) integration tests verify that the Another-Intelligence `MCPClient` can connect to real MCP servers over stdio, discover tools, execute them, and enforce permissions.

These tests live in `tests/mcp/test_mcp_integration.py` and require **Node.js** with `npx` on PATH.

## Prerequisites

```bash
# Verify Node.js and npx are available
node --version   # v20+
npx --version
```

If missing, install Node.js via your system package manager or `nvm`.

## Test Servers

The integration suite uses three official reference servers from `@modelcontextprotocol`:

| Server       | Package                      | Purpose                            |
| ------------ | ---------------------------- | ---------------------------------- |
| **fs**       | `server-filesystem`          | Read files from a scoped directory |
| **memory**   | `server-memory`              | Key-value memory store             |
| **thinking** | `server-sequential-thinking` | Step-by-step reasoning             |

These servers are installed on-demand via `npx -y` — no manual `npm install` required.

## Running the Tests

```bash
# Full MCP integration suite (takes ~60s, includes npx install time)
uv run pytest tests/mcp/test_mcp_integration.py -v

# Individual test class
uv run pytest tests/mcp/test_mcp_integration.py::TestStdioConnection -v
uv run pytest tests/mcp/test_mcp_integration.py::TestMCPClientIntegration -v

# With extended timeout (first run may download packages)
timeout 120 uv run pytest tests/mcp/test_mcp_integration.py -v
```

Tests are **automatically skipped** if `npx` is not found on PATH.

## What Each Test Covers

### `TestStdioConnection`

| Test                          | Validates                                                                                                      |
| ----------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `test_connect_and_list_tools` | `StdioConnection.connect()` initializes JSON-RPC session and `list_tools()` returns non-empty tool definitions |
| `test_read_file`              | `call_tool("read_file", {...})` reads a known temp file and returns its content                                |

### `TestMCPClientIntegration`

| Test                              | Validates                                                           |
| --------------------------------- | ------------------------------------------------------------------- |
| `test_connect_all`                | `MCPClient.connect_all()` connects to every server in the registry  |
| `test_list_tools_via_client`      | Tool caching and discovery through the client API                   |
| `test_call_tool_with_permissions` | Permissive `PermissionEngine` allows `mcp.fs.read_file`             |
| `test_call_tool_denied`           | Deny-all `PermissionEngine` blocks execution with correct error     |
| `test_hooks_fire`                 | `PreToolUse`, `PostToolUse`, and `MCPToolCalled` events are emitted |
| `test_tool_cache`                 | Repeated `list_tools()` calls use the in-memory cache               |

## Test Architecture

```
pytest fixture (tmp_path)
    ├─ Creates temp directory with "hello.txt"
    ├─ Writes mcp.json pointing filesystem server at temp dir
    ├─ Builds PermissionConfig → JSON → temp file → PermissionEngine
    └─ Provides MCPRegistry + PermissionEngine to test

Test
    ├─ StdioConnection(config)  ← real asyncio subprocess
    ├─ await conn.connect()     ← JSON-RPC initialize + notifications/initialized
    ├─ await conn.list_tools()  ← "tools/list" request
    ├─ await conn.call_tool(...)← "tools/call" request
    └─ await conn.disconnect()  ← terminate subprocess
```

## Configuration

The tests use a **temporary** `mcp.json` generated per test run. For production usage, place `mcp.json` in one of:

- `~/.brainxio/mcp.json` — global config
- `.brainxio/mcp.json` — project-level config (gitignored)

Example `.brainxio/mcp.json`:

```json
{
  "servers": [
    {
      "name": "fs",
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "."],
      "permissions": ["filesystem.read"],
      "timeout": 30.0
    }
  ]
}
```

## Known Limitations

- **First run is slow**: `npx -y` downloads the MCP server on first use (~10–20s).
- **Event loop warnings**: pytest-asyncio may emit resource warnings about closed event loops after subprocess cleanup. These are harmless.
- **No Docker required**: All servers are pure Node.js and run over stdio.

## Troubleshooting

### `Method not found` on connect

The MCP spec requires `notifications/initialized` to be sent as a **notification** (no JSON-RPC `id`). If the client sends it as a request, the server returns `-32601`. This is handled correctly in `StdioConnection.connect()` via `send_notification()`.

### Permission denied on all calls

Ensure the `PermissionEngine` is initialized from a JSON file containing the grants:

```json
{
  "permissions": {
    "grants": [
      {"capability": "mcp.fs.*", "allowed_by": "test"}
    ]
  }
}
```

### Server timeout

Increase `timeout` in `MCPServerConfig` if running on a slow network or Raspberry Pi.
