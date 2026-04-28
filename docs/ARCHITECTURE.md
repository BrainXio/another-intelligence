---
title: "Another-Intelligence Architecture"
version: "0.1"
status: draft
updated: "2026-04-28"
---

# Another-Intelligence Architecture

## 1. Vision & Goals

**Another-Intelligence** is a **persistent, neuroscience-grounded digital brain** that makes decisions the way biological brains do — through a strict serial **PPAC loop** (Proposer → Predictor → Accumulator → Actor → Critic) — while remaining fully independent of any proprietary agent SDK.

### Core Goals
- **True independence**: Runs 100% on Ollama (Python + JS clients) with no Claude Code SDK dependency.
- **Neuroscience fidelity**: Every decision flows through five biologically-modeled regions with real RPE-driven learning.
- **Modular & extensible**: Clean core + pluggable extensions via a first-class **MCP (Model Context Protocol)** client.
- **Permissions-first & secure**: Capability-based permissions + typed hook system that replaces Claude SDK hooks.
- **Maintainable for all levels**: Clear architecture, excellent documentation, and TDD so beginners and experts can contribute.
- **Self-improving**: Continuous RPE-based learning with automated dataset generation for QLoRA fine-tuning.

---

## 2. Architectural Principles

1. **Neuroscience First** — Every major component maps to biological mechanisms (PFC, Limbic, Parietal LIP, Basal Ganglia Go/NoGo, Dopamine RPE).
2. **Strict Serial PPAC** — No shortcuts. All five stages execute in order for every decision.
3. **Core + Extensions** — Minimal core. Everything else (eyes, voice, hardware, browser automation, custom tools) is a plugin or MCP server.
4. **MCP-Native** — Model Context Protocol is a first-class citizen. Any compliant MCP server (Puppeteer, Playwright, Filesystem, Git, Memory, etc.) works out of the box.
5. **Permissions & Hooks as First-Class** — Security and extensibility are designed in, not bolted on.
6. **Configuration over Code** — Behavior is driven by `~/.brainxio/` (global) and `.brainxio/` (project) — mirroring the best of `.claude` while remaining fully open.
7. **Observable by Default** — Every region, tool call, RPE update, and context change emits events.
8. **Test-Driven & Autonomous** — The architecture is designed so a Claude-agent-sdk (running on our own models) can implement large parts with minimal human intervention once baseline documents exist.

---

## 3. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Another-Intelligence                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐    │
│   │   DigitalBrain   │────▶│   PPAC Loop      │────▶│   5 Brain Regions│    │
│   │   (Orchestrator) │     │   (Strict Serial)│     │   (Strategist,   │    │
│   └──────────────────┘     └──────────────────┘     │    Executor,     │    │
│                                                     │    Reflex)       │    │
│   ┌──────────────────┐     ┌──────────────────┐     └──────────────────┘    │
│   │   Permissions    │◀────│   Hook System    │                             │
│   │   Engine         │     │   (Typed Events) │                             │
│   └──────────────────┘     └──────────────────┘                             │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                        MCP Client (Core)                            │   │
│   │  • Puppeteer / Playwright  • Filesystem  • Git  • Memory  • Custom  │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│   ┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐    │
│   │   Knowledge      │     │   RPE + Memory   │     │   Plugin Loader  │    │
│   │   Pipeline       │     │   Value Index    │     │   (Core + Ext)   │    │
│   └──────────────────┘     └──────────────────┘     └──────────────────┘    │
│                                                                             │
│   Configuration: ~/.brainxio/  +  .brainxio/ (project)                      │
│   Models: Another-Intelligence/strategist, /executor, /reflex (tiered)      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Core Components

### 4.1 DigitalBrain (Orchestrator)
- Entry point for all decisions (`decide()`, `daydream()`, `introspect()`).
- Manages session lifecycle, context window tracking, and event emission.
- Delegates to PPAC loop and routes tool calls through Permissions + Hooks.

### 4.2 PPAC Loop (Strict Serial)
1. **Strategist** (PFC / DLPFC-OFC) — Proposes options, computes multi-attribute expected value.
2. **Executor** (Limbic + Basal Ganglia) — Emotional valence tagging + Go/NoGo selection.
3. **Reflex** (Parietal LIP + Dopamine) — Noisy evidence accumulation + RPE computation.
4. **Outcome Recording** — Real external feedback → RPE = actual − expected.
5. **Learning** — Memory-value index update + preference dataset generation (when |RPE| > threshold).

### 4.3 Model Layer
- Unified Ollama client abstraction (Python primary, JS where needed).
- Supports tiered models (`:cloud-max`, `:cloud-pro`, local GGUF).
- Automatic context-length handling and structured outputs + tool calling.

### 4.4 Permissions Engine
- Capability-based (not just allow/deny lists).
- Declarative policies in `settings.json`.
- PreToolUse hooks can influence decisions but cannot bypass explicit deny rules.

### 4.5 Hook System
Typed events:
- `SessionStart`, `SessionEnd`, `PreToolUse`, `PostToolUse`
- `BrainRegionActivated`, `RPEUpdated`, `ContextWindowChanged`
- `PermissionRequested`, `MCPToolCalled`

Hooks are registered in `~/.brainxio/settings.json` or project `.brainxio/settings.json` and can be shell commands, Python callables, or MCP tools.

### 4.6 MCP Client (First-Class)
- Native MCP 2025/2026 client.
- Auto-discovery of local MCP servers via `mcp.json`.
- Transparent tool calling: models see MCP tools the same as native tools.
- Security: MCP tools go through the same Permissions + Hook pipeline.

### 4.7 Knowledge & Memory
- Daily logs → `ai compile` → structured articles (concepts, mechanisms, outcomes).
- `memory-value index` (context + option → learned value).
- Long-term episodic store (pluggable via MCP Memory server or local vector DB).

### 4.8 Plugin System
- Core plugins (eyes, voice, hardware) live in `src/another_intelligence/plugins/`.
- Third-party plugins installed via `uv pip install another-intelligence-plugin-foo`.
- Hot-reload support during development.

---

## 5. Configuration (`~/.brainxio/` + `.brainxio/`)

Mirrors the proven `.claude` model with improvements for clarity:

```
~/.brainxio/                    # Global (user-wide)
├── settings.json               # Permissions, model defaults, MCP servers, hooks
├── settings.local.json         # Gitignored personal overrides
├── rules/                      # Modular instruction fragments (loaded in order)
├── skills/                     # Reusable workflows (SKILL.md)
├── agents/                     # Specialized sub-personas
├── mcp.json                    # MCP server registry
├── memory/                     # Long-term index
└── docs/

.brainxio/                      # Project-level (committed)
├── settings.json
├── rules/
├── skills/
└── agents/
```

---

## 6. Technology Choices

| Layer              | Technology                  | Rationale |
|--------------------|-----------------------------|---------|
| Core Runtime       | Python 3.12+ (uv)           | Best ecosystem for agents, MCP, scientific computing |
| JS Layer           | Node + npm/pnpm             | Browser automation, web UI, certain extensions |
| LLM Client         | `ollama` (Python) + `@ollama/ollama` (JS) | Official, actively maintained, full tool calling + structured outputs |
| Testing            | pytest + Vitest + Playwright | TDD + browser automation via MCP |
| Async              | asyncio + anyio             | Clean concurrency across regions and tools |
| Configuration      | Pydantic Settings + JSON    | Type-safe, validated, easy to extend |
| Plugin System      | importlib + entry points    | Standard Python packaging, discoverable |
| Event Bus          | Simple typed event emitter  | Lightweight, observable, easy to hook |

---

## 7. Security & Governance Model

- **Capability-based permissions** — Agents/tools only receive the capabilities they are explicitly granted.
- **Least privilege by default** — New MCP servers or plugins start with zero permissions.
- **Audit logging** — Every tool call, permission decision, and hook execution is logged immutably.
- **Human-in-the-loop** — Configurable ask/deny thresholds for high-impact actions.
- **Sandboxing** — MCP servers and plugins run with restricted filesystem/network access where possible.

---

## 8. Extensibility Story

**Three ways to extend Another-Intelligence** (in order of preference):

1. **MCP Server** (Recommended) — Write a small MCP server in any language. Works immediately with zero code changes in core.
2. **Python Plugin** — Implement the `Plugin` protocol. Can add new brain regions, tools, or display backends.
3. **Hook + Skill** — Pure configuration + prompt engineering for most workflow changes.

This design ensures the core stays small and stable while the ecosystem can grow rapidly.

---

## 9. Relationship to Current Prototype

The existing `ai_brain` / Claude-infused codebase in `~/work/_meta` is treated as **reference implementation and inspiration only**. No code will be ported. The new `another-intelligence` package under `~/work/projects/another-intelligence` is a clean-slate implementation that re-creates the *concepts* (PPAC, RPE, eyes, knowledge pipeline, hooks) using the architecture described in this document.

---

**End of ARCHITECTURE.md**

*This document is the single source of truth for architectural decisions. All other documents (BASELINE.md, HOOKS.md, etc.) must remain consistent with it.*
