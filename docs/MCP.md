______________________________________________________________________

## title: "Model Context Protocol Integration" version: "0.1" status: draft updated: "2026-04-28"

# MCP.md — Model Context Protocol Integration

## Purpose

MCP (Model Context Protocol) is a **first-class extensibility mechanism** in Another-Intelligence. It allows the brain to securely and uniformly interact with external tools, services, and capabilities (filesystem, browser, git, memory stores, hardware, etc.) without hardcoding them into the core.

This document defines how MCP is integrated, configured, secured, and extended.

______________________________________________________________________

## 1. Why MCP is First-Class

- Decouples core brain logic from specific tools.
- Enables zero-code extension: just run an MCP server and register it.
- Provides consistent permission, hook, and observability treatment for all external capabilities.
- Supports both local and remote MCP servers.
- Aligns with the 2025–2026 ecosystem (Puppeteer, Playwright, Filesystem, Git, Memory, Serena, etc.).

______________________________________________________________________

## 2. Architecture Overview

```
DigitalBrain
     ↓ (tool call)
Permissions Engine → PreToolUse Hook
     ↓
MCP Client (core)
     ↓
MCP Server Registry (from ~/.brainxio/mcp.json)
     ↓
Individual MCP Servers (Puppeteer, Filesystem, etc.)
     ↓
PostToolUse Hook + RPE contribution
```

______________________________________________________________________

## 3. Configuration (`mcp.json`)

Global: `~/.brainxio/mcp.json`\
Project: `.brainxio/mcp.json`

```json
{
  "servers": [
    {
      "name": "filesystem",
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/allowed-dir"],
      "permissions": ["filesystem.read", "filesystem.write:scoped"]
    },
    {
      "name": "puppeteer",
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-puppeteer"],
      "permissions": ["browser.navigate", "browser.screenshot"]
    },
    {
      "name": "git",
      "type": "stdio",
      "command": "python",
      "args": ["-m", "another_intelligence.mcp.git_server"],
      "permissions": ["git.read", "git.commit"]
    }
  ]
}
```

______________________________________________________________________

## 4. MCP Client Implementation

- Located in `src/another_intelligence/mcp/client.py`
- Uses official MCP Python/JS client libraries.
- Auto-discovers and connects to all configured servers at `SessionStart`.
- Caches tool definitions per session.
- All tool calls go through:
  1. Permissions check
  2. PreToolUse hooks
  3. Execution
  4. PostToolUse hooks
  5. RPE contribution (if outcome affects learning)

______________________________________________________________________

## 5. Tool Calling Flow

When a model (Strategist/Executor/Reflex) wants to use a tool:

1. Model outputs a structured tool call.
2. Core routes it to MCP Client.
3. Permissions Engine validates the capability.
4. PreToolUse hooks run (can modify or veto).
5. MCP Client executes the tool on the correct server.
6. Result is returned to the model + PostToolUse hooks fire.
7. If the tool produced a measurable outcome → RPE can be computed.

______________________________________________________________________

## 6. Built-in / Recommended MCP Servers

| Server               | Purpose                           | Recommended Implementation     | Default Permissions  |
| -------------------- | --------------------------------- | ------------------------------ | -------------------- |
| filesystem           | Safe file operations              | Official @modelcontextprotocol | Scoped read/write    |
| puppeteer/playwright | Browser automation & testing      | Official                       | Limited navigation   |
| git                  | Repository operations             | Custom lightweight             | Read + scoped commit |
| memory               | Long-term episodic / vector store | Custom or LanceDB-based        | Read/write index     |
| hardware             | GPIO, sensors, device control     | Custom                         | Hardware.\*          |
| serena               | Code intelligence & refactoring   | Official / community           | Code.\*              |

______________________________________________________________________

## 7. Security Model for MCP

- Every server starts with **zero permissions**.
- Permissions must be explicitly granted in `mcp.json`.
- Scoped permissions supported (e.g., `filesystem.write:/home/user/projects`).
- All MCP calls are logged with full context in the brain activity log.
- Rate limiting and timeout per server configurable.
- Human confirmation configurable for high-impact capabilities.

______________________________________________________________________

## 8. Developing a New MCP Server

1. Create a new server following the official MCP spec (any language).
2. Add it to `mcp.json`.
3. Grant minimal required permissions.
4. Test with `ai mcp test <server-name> <tool-name>` (future CLI command).
5. Document capabilities in `docs/MCP-SERVERS.md` (optional).

Example minimal Python MCP server skeleton is provided in `src/another_intelligence/mcp/templates/`.

______________________________________________________________________

## 9. Testing MCP Integration

```bash
# List available MCP tools
ai mcp list

# Test a specific tool
ai mcp call filesystem.read --args '{"path": "README.md"}'

# Run MCP-specific test suite
uv run pytest tests/mcp/
```

______________________________________________________________________

## 10. Relationship to Other Systems

- **Permissions.md** — All MCP tools are governed by the capability system.
- **HOOKS.md** — MCP calls trigger PreToolUse / PostToolUse / MCPToolCalled.
- **ARCHITECTURE.md** — MCP Client is part of the core, not a plugin.

______________________________________________________________________

**This document is the definitive reference for all MCP usage and extension in Another-Intelligence.**
