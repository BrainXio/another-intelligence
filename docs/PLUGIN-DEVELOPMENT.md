# PLUGIN-DEVELOPMENT.md — Plugin System Guide

**Version:** 0.1 (Draft)  
**Status:** Living Document  
**Last Updated:** 2026-04-28

---

## Purpose

This document explains how to develop, install, and distribute plugins for Another-Intelligence. The plugin system allows anyone to extend the brain with new capabilities (display backends, voice, hardware integration, custom agents, etc.) while keeping the core small and stable.

---

## 1. Plugin Architecture Principles

- **Lightweight Core** — Only essential brain loop, permissions, hooks, and MCP live in the main package.
- **Discoverable** — Plugins use Python entry points + optional `~/.brainxio/plugins/` directory.
- **Permission-Aware** — Every plugin must declare required capabilities.
- **Hot-Reload Friendly** — Useful during development.
- **Versioned & Isolated** — Plugins can specify compatible core versions.

---

## 2. Plugin Types

| Type              | Purpose                              | Example |
|-------------------|--------------------------------------|--------|
| **Display**       | Eyes / statusline backends           | `eyes-gtk`, `eyes-web` |
| **Voice**         | TTS / STT engines                    | `voice-piper`, `voice-whisper` |
| **Hardware**      | Device integration                   | `hardware-raspberrypi` |
| **Agent**         | New brain region or specialized agent| `agent-vision` |
| **MCP**           | Bundled MCP server                   | `mcp-memory` |
| **Skill**         | Reusable workflow (prompt + tools)   | `skill-research` |

---

## 3. Creating a Plugin

### Step-by-step

1. **Scaffold a new plugin**

```bash
uv tool run cookiecutter https://github.com/brainxio/plugin-template
# or manually create:
# another-intelligence-plugin-eyes-gtk/
```

2. **Minimal plugin structure**

```
another-intelligence-plugin-eyes-gtk/
├── pyproject.toml
├── src/
│   └── another_intelligence_plugin_eyes_gtk/
│       ├── __init__.py
│       ├── plugin.py
│       └── gtk_backend.py
├── README.md
└── capabilities.json          # Declared permissions
```

3. **Plugin entry point** (`plugin.py`)

```python
from another_intelligence.plugins import Plugin, register_plugin

@register_plugin("display.eyes.gtk")
class GtkEyesPlugin(Plugin):
    name = "GTK Eyes Backend"
    version = "0.1.0"
    requires = ["display.eyes"]
    capabilities = ["display.render.gtk"]

    async def load(self, brain):
        # Register backend with DisplayController
        ...
```

4. **Declare capabilities** (`capabilities.json`)

```json
{
  "required": ["display.eyes"],
  "provided": ["display.render.gtk"]
}
```

---

## 4. Installing Plugins

```bash
# From source
uv pip install -e /path/to/another-intelligence-plugin-xxx

# From PyPI (future)
uv pip install another-intelligence-plugin-eyes-gtk
```

The plugin loader auto-discovers all installed plugins at `SessionStart`.

---

## 5. Plugin Lifecycle

- `load(brain)` — Called during SessionStart
- `unload()` — Called during SessionEnd (cleanup)
- `on_event(event)` — Optional: receive any brain event
- `provide_tools()` — Can expose additional MCP-style tools

---

## 6. Development Workflow for Plugins

```bash
# Inside plugin directory
uv venv
uv pip install -e ".[dev]"          # includes core as editable dependency

# Test with local core
uv run pytest
```

Use the same TDD approach as the main project.

---

## 7. Publishing a Plugin

- Publish to PyPI with prefix `another-intelligence-plugin-*`
- Add to official plugin registry (future `brainxio.org/plugins`)
- Include clear `capabilities.json` and documentation
- Follow semantic versioning

---

## 8. Example Plugins (Planned)

- `another-intelligence-plugin-eyes-web` (WebSocket + browser frontend)
- `another-intelligence-plugin-voice-piper`
- `another-intelligence-plugin-hardware-rpi`
- `another-intelligence-plugin-mcp-memory`

---

## 9. Best Practices

- Keep plugins small and focused (single responsibility).
- Always declare exact capabilities needed.
- Provide graceful degradation if optional dependencies are missing.
- Include comprehensive tests and example configurations.
- Update `PLUGIN-DEVELOPMENT.md` if new conventions emerge.

---

**This document is the official guide for extending Another-Intelligence.**  
All new plugins must follow this structure and be consistent with `ARCHITECTURE.md`, `PERMISSIONS.md`, and `MCP.md`.

**Next documents in alphabetical order:** `PROMPTING.md`, `README.md`, `ROADMAP.md`
