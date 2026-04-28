# HOOKS.md — Hook System Specification

**Version:** 0.1 (Draft)  
**Status:** Living Document  
**Last Updated:** 2026-04-28

---

## Purpose

The hook system provides a secure, extensible, and observable way to extend or modify behavior at key points in the lifecycle of Another-Intelligence — without modifying core code. It fully replaces the functionality previously provided by the Claude SDK hooks while being completely independent and permission-aware.

---

## 1. Design Principles

- **Typed & Observable** — Every hook is a named event with a well-defined data contract.
- **Permission-Gated** — Hooks cannot bypass the permissions engine.
- **Multi-Implementation** — A hook can be handled by shell scripts, Python callables, or MCP tools.
- **Composable** — Multiple hooks can run for the same event (in registration order).
- **Safe by Default** — Hooks run with least-privilege context; dangerous operations require explicit permission grants.
- **Debuggable** — Every hook execution is logged with full input/output and timing.

---

## 2. Core Hook Events

| Event                  | Trigger Point                          | Payload (Pydantic Model)                  | Use Cases |
|------------------------|----------------------------------------|-------------------------------------------|---------|
| **SessionStart**       | Before any decision or tool use        | `SessionContext` (user, tier, model, etc.) | Inject knowledge, load rules, detect tier |
| **SessionEnd**         | After session completes                | `SessionSummary` (decisions, RPEs, etc.)  | Flush memory, compile knowledge |
| **PreToolUse**         | Before any tool / MCP call             | `ToolRequest` (tool name, args, caller)   | Permission check, logging, modification |
| **PostToolUse**        | After tool / MCP call returns          | `ToolResult` (success, result, duration)  | Post-processing, RPE contribution |
| **BrainRegionActivated**| When a region starts/finishes          | `RegionEvent` (region, input, output)     | Statusline, eyes animation, logging |
| **RPEUpdated**         | After outcome recorded                 | `RPEEvent` (rpe_value, context_key, etc.) | Trigger dataset generation |
| **ContextWindowChanged**| When context usage crosses thresholds  | `ContextUsage` (used, total, percentage)  | Warning, compaction |
| **MCPToolCalled**      | When an MCP server tool is invoked     | `MCPToolEvent`                             | Auditing MCP-specific calls |
| **PermissionRequested**| When permissions engine evaluates      | `PermissionRequest`                        | Custom approval flows |

---

## 3. Hook Registration

Hooks are declared in `~/.brainxio/settings.json` and `.brainxio/settings.json` (project).

```json
{
  "hooks": {
    "SessionStart": [
      { "type": "shell", "command": "ai hook session-start" },
      { "type": "python", "entry_point": "another_intelligence.hooks.session_start" },
      { "type": "mcp", "server": "memory", "tool": "inject_recent_episodes" }
    ],
    "PreToolUse": [
      { "type": "python", "entry_point": "another_intelligence.hooks.pre_tool_guard" }
    ]
  }
}
```

**Merging rule**: Global settings are loaded first, then project overrides can append or replace.

---

## 4. Hook Execution Contract

For every hook:

1. Permissions engine checks if the hook implementation has the required capability (`hook.execute.<event>`).
2. Hook is called with typed payload (Pydantic model).
3. Execution is timed and logged.
4. If a hook raises an exception:
   - Non-critical hooks → logged as warning.
   - Critical hooks (e.g. PreToolUse) → can veto the action.
5. Post-hook: `PostToolUse` or equivalent fires if applicable.

---

## 5. Implementation Interfaces

### Python Hook (Recommended for complex logic)
```python
from another_intelligence.hooks import HookContext, register_hook

@register_hook("PreToolUse")
async def pre_tool_guard(ctx: HookContext):
    if ctx.payload.tool_name.startswith("dangerous:"):
        return {"action": "deny", "reason": "Restricted tool"}
    return {"action": "allow"}
```

### Shell Hook (Simple & fast)
Just an executable that reads JSON from stdin and writes JSON to stdout.

### MCP Hook
Delegates to an MCP server tool — automatically permission-checked.

---

## 6. Security Model

- Hooks run in the same process as the core (Python) or as subprocesses (shell).
- Subprocesses are sandboxed where possible (limited env, no network unless granted).
- All hook output is validated against the expected schema.
- High-impact hooks (SessionStart with model changes, PreToolUse) require explicit user confirmation if configured.

---

## 7. Built-in Hooks (Core)

The following hooks ship with the core package:

- `session_start.py` — Injects knowledge index, rules, and tier detection.
- `session_end.py` — Triggers flush and knowledge compilation.
- `pre_tool_guard.py` — Default permission enforcement + logging.
- `rpe_handler.py` — Generates training datasets on high |RPE|.
- `statusline_updater.py` — Updates real-time status and eyes animation.

---

## 8. Testing Hooks

```bash
# Test a specific hook
ai hook test PreToolUse --payload '{"tool_name": "filesystem.read"}'

# Run full hook test suite
uv run pytest tests/hooks/
```

---

## 9. Migration from Claude SDK

Existing Claude hooks can be mapped 1:1:
- `session-start` → `SessionStart`
- `pre-compact` → `PreToolUse` + `ContextWindowChanged`
- `session-end` → `SessionEnd`

No direct port of code — only concepts.

---

**This document is the definitive specification.**  
Any new hook event must be added here first and kept consistent with `ARCHITECTURE.md` and `PERMISSIONS.md`.

**Next documents in alphabetical order:** `MCP.md`, `MIGRATION.md`, `PERMISSIONS.md`
