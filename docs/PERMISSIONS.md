# PERMISSIONS.md — Capability-Based Permissions System

**Version:** 0.1 (Draft)  
**Status:** Living Document  
**Last Updated:** 2026-04-28

---

## Purpose

The permissions system is a **core security layer** that enforces least-privilege access for all tools, MCP servers, hooks, and plugins. It replaces any implicit trust from the Claude SDK with explicit, auditable, capability-based control.

---

## 1. Design Principles

- **Capability-Based** (not role-based) — Grants are specific actions (e.g., `filesystem.read`, `browser.navigate`).
- **Least Privilege by Default** — Everything starts denied.
- **Declarative & Auditable** — Policies are defined in JSON and logged on every decision.
- **Human-in-the-Loop Capable** — Configurable escalation for sensitive actions.
- **Hook-Aware** — PreToolUse hooks can influence but never bypass explicit denies.
- **Scoped** — Many capabilities support fine-grained scoping (paths, domains, etc.).

---

## 2. Permission Structure

Each permission follows the pattern: `category.action[:scope]`

### Examples
- `filesystem.read`
- `filesystem.write:/home/user/projects/another-intelligence`
- `browser.navigate`
- `git.commit`
- `hardware.gpio`
- `mcp.call:filesystem`
- `hook.execute:PreToolUse`

---

## 3. Configuration (`settings.json`)

```json
{
  "permissions": {
    "default_policy": "deny",
    "grants": [
      {
        "capability": "filesystem.read",
        "scope": "/home/user/projects",
        "allowed_by": "global"
      },
      {
        "capability": "browser.navigate",
        "allowed_by": "project",
        "require_confirmation": true
      }
    ],
    "escalation": {
      "high_impact": ["filesystem.write:*", "git.push", "hardware.*"],
      "require_user_approval": true
    }
  }
}
```

Global (`~/.brainxio/settings.json`) + project (`.brainxio/settings.json`) merge with project taking precedence on conflicts.

---

## 4. Permission Evaluation Flow

1. Tool / MCP call requested.
2. Permissions Engine looks up the exact capability.
3. If explicitly denied → immediate rejection.
4. If not granted → check default_policy (deny).
5. If granted → run PreToolUse hooks (can add temporary restrictions).
6. If escalation rule matches → request human confirmation (configurable).
7. Execute → log decision with full context.
8. PostToolUse hook fires.

---

## 5. Core Capabilities (Built-in)

| Category          | Capabilities                                      | Default |
|-------------------|---------------------------------------------------|---------|
| filesystem        | read, write, list, delete                         | deny |
| browser           | navigate, screenshot, click, type                 | deny |
| git               | read, commit, push, clone                         | deny |
| mcp               | call:<server>                                     | deny |
| hook              | execute:<event>                                   | allow (limited) |
| knowledge         | read, write, compile                              | allow |
| model             | switch_tier, change_context                       | deny |
| hardware          | gpio, sensors, audio                              | deny |
| training          | generate_dataset, trigger_fine_tune               | deny |

---

## 6. Python API

```python
from another_intelligence.permissions import PermissionEngine, requires

engine = PermissionEngine()

@requires("filesystem.write:/tmp")
async def safe_write(path: str, content: str):
    ...
```

---

## 7. Testing Permissions

```bash
# Test a permission decision
ai permissions check filesystem.write:/tmp --explain

# Run permission test suite
uv run pytest tests/permissions/
```

---

## 8. Security Best Practices

- Grant the minimal set of capabilities needed for each session.
- Use scoped permissions wherever possible.
- Review `~/.brainxio/settings.json` regularly.
- High-impact actions should require confirmation.
- All permission decisions are immutable in the brain activity log.

---

## 9. Relationship to Other Systems

- **MCP.md** — All MCP tools are routed through this engine.
- **HOOKS.md** — PreToolUse can influence permission outcomes.
- **ARCHITECTURE.md** — Permissions is a core component, not optional.

---

**This document defines the security boundary of Another-Intelligence.**  
Any new capability must be added here first and given a clear default policy.

**Next documents in alphabetical order:** `PLUGIN-DEVELOPMENT.md`, `PROMPTING.md`, `README.md`
