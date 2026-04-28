# Product Requirements Document — Another-Intelligence v0.1

---
version: "0.1"
status: draft
updated: "2026-04-28"
---

## 1. Overview

**Another-Intelligence** is a fully independent, Ollama-native cognitive architecture that models biological decision-making through a strict serial PPAC loop (Proposer → Predictor → Accumulator → Actor → Critic).

It replaces any dependency on proprietary agent SDKs with a clean, testable, neuroscience-grounded core that learns from real Reward Prediction Error (RPE) and improves over time.

## 2. Goals

- **True independence**: 100% Ollama-based, zero dependency on Claude SDK or any proprietary LLM API.
- **Neuroscience fidelity**: Every decision flows through five biologically-modeled brain regions with real RPE-driven learning.
- **MCP-native extensibility**: Model Context Protocol is a first-class citizen for all external tools.
- **Permission-first security**: Capability-based permissions with least-privilege defaults.
- **Autonomous development ready**: Designed for heavy use with Claude-agent-sdk + MCP servers.
- **Self-improving**: Continuous RPE-based learning with automated dataset generation for future fine-tuning.

## 3. Scope (v0.1)

### In Scope

- Core Python package with uv tooling
- Strict serial PPAC loop with all five stages
- Three Ollama model roles: Strategist, Executor, Reflex
- Tiered model resolution (Max, Pro, Free, Local)
- Capability-based permissions engine
- Typed hook system with lifecycle events
- Native MCP client with auto-discovery
- Context window tracking and system metrics
- Event-driven observability (statusline, activity logger)
- `~/.brainxio/` and `.brainxio/` configuration system
- Basic knowledge pipeline (`ai compile`, `ai query`)
- `ai` CLI entry point with core commands
- Full test suite (pytest) with ≥ 70% core coverage

### Out of Scope (Deferred to v0.2+)

- Self-fine-tuning loop (trainer node, QLoRA)
- Production-grade display/eyes and voice plugins
- Multi-user / multi-tenant support
- GUI installer or one-click setup
- Full plugin marketplace

## 4. Architecture

### 4.1 High-Level Components

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Another-Intelligence                           │
├─────────────────────────────────────────────────────────────────────────────┤
│  DigitalBrain (Orchestrator)                                                │
│    ├── PPAC Loop (strict serial)                                            │
│    │    ├── Strategist (PFC/DLPFC-OFC)                                      │
│    │    ├── Executor (Limbic + Basal Ganglia)                               │
│    │    └── Reflex (Parietal LIP + Dopamine)                                │
│    ├── Permissions Engine                                                   │
│    ├── Hook System (typed events)                                           │
│    ├── MCP Client (first-class)                                             │
│    ├── Knowledge Pipeline                                                   │
│    ├── RPE + Memory Value Index                                             │
│    └── Plugin Loader                                                        │
│                                                                             │
│  Configuration: ~/.brainxio/ + .brainxio/                                   │
│  Models: Another-Intelligence/strategist, /executor, /reflex                │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 PPAC Loop Sequence

1. **Strategist** (PFC) — Proposes options, computes multi-attribute expected value.
2. **Executor** (Limbic + Basal Ganglia) — Emotional valence tagging + Go/NoGo selection.
3. **Reflex** (Parietal + Dopamine) — Noisy evidence accumulation + RPE computation.
4. **Outcome Recording** — Real external feedback → `RPE = actual − expected`.
5. **Learning** — Memory-value index update + preference dataset generation (when `|RPE| > 0.3`).

Each stage completes before the next begins. Complex decisions cycle through multiple iterations.

### 4.3 Configuration System

```
~/.brainxio/                    # Global (user-wide)
├── settings.json               # Permissions, model defaults, MCP servers, hooks
├── settings.local.json         # Gitignored personal overrides
├── rules/                      # Modular instruction fragments (loaded alphabetically)
├── skills/                     # Reusable workflows (SKILL.md)
├── agents/                     # Specialized sub-personas
├── mcp.json                    # MCP server registry
├── memory/                     # Long-term episodic store index
└── docs/

.brainxio/                      # Project-level (committed)
├── settings.json
├── rules/
├── skills/
└── agents/
```

## 5. Functional Requirements

### 5.1 PPAC Decision Loop

- FR-1.1: All five brain regions execute in strict serial order for every `decide()` call.
- FR-1.2: The loop completes successfully on at least 10 diverse test prompts covering:
  - Simple factual queries
  - Multi-step planning
  - Tool-using tasks
  - Multi-turn conversations (minimum 5 turns)
  - Creative / open-ended prompts
- FR-1.3: Context key consistency is enforced: the key used in `propose()` must match the key used in `record_outcome()`.

### 5.2 Brain Regions

- FR-2.1: Strategist produces structured proposals with multi-attribute expected values.
- FR-2.2: Executor correctly assigns emotional valence and performs Go/NoGo selection.
- FR-2.3: Reflex performs noisy evidence accumulation and computes RPE.
- FR-2.4: Each region emits a `BrainRegionActivated` event with correct metadata (region name, timestamp, input summary, output summary).

### 5.3 Outcome Recording & Learning

- FR-3.1: Real external outcomes (test results, user feedback, system metrics) are captured and used to compute `RPE = actual − expected`.
- FR-3.2: When `|RPE| > 0.3`, a valid preference pair (chosen / rejected) is exported to `~/.brainxio/training_datasets/`.
- FR-3.3: Memory-value index is updated correctly after every outcome.

### 5.4 Observability & Monitoring

- FR-4.1: Real-time context window usage is tracked and exposed via API and statusline (accurate to ±5% of actual tokens used).
- FR-4.2: System metrics (CPU, memory, model latency, tokens per second) are collected and displayed.
- FR-4.3: Activity state machine correctly reflects current phase (Idle, Proposing, Accumulating, Selecting, Learning, etc.).
- FR-4.4: Event log (`~/.brainxio/state/brain_activity.jsonl`) is append-only and contains every major event.
- FR-4.5: `ai status --extended` shows live brain state, latest RPE, active regions, and context usage.

### 5.5 Security & Permissions

- FR-5.1: Capability-based permissions engine is implemented and active.
- FR-5.2: Default policy is least privilege (new tools/MCP servers start with zero permissions).
- FR-5.3: `settings.json` supports declarative allow / ask / deny rules per tool and per capability.
- FR-5.4: PreToolUse hooks can influence permission decisions but cannot bypass an explicit deny rule.
- FR-5.5: All permission decisions are logged with full context (who, what, why, outcome).

### 5.6 Hook System

- FR-6.1: Typed event system supports at minimum: `SessionStart`, `SessionEnd`, `PreToolUse`, `PostToolUse`, `BrainRegionActivated`, `RPEUpdated`, `MCPToolCalled`.
- FR-6.2: Hooks can be registered via `~/.brainxio/settings.json` or project `.brainxio/settings.json`.
- FR-6.3: Hooks can be implemented as shell commands, Python callables (entry points), or MCP tools.
- FR-6.4: Hook execution is observable and logged.

### 5.7 MCP Integration

- FR-7.1: Native MCP client is implemented in core.
- FR-7.2: At least 3 MCP servers are successfully registered and callable: Filesystem, Browser (Puppeteer/Playwright), and one additional (Git, Memory, or custom).
- FR-7.3: MCP tools appear to the model identically to native tools.
- FR-7.4: MCP tool calls go through the full Permissions + Hook pipeline.
- FR-7.5: `mcp.json` configuration is supported for both global (`~/.brainxio/`) and project (`.brainxio/`) scope.

### 5.8 Knowledge & Configuration

- FR-8.1: `ai compile` successfully parses daily logs and produces structured articles.
- FR-8.2: `ai query` returns relevant results from the compiled knowledge base.
- FR-8.3: `~/.brainxio/` and `.brainxio/` directory structure is fully functional (settings, rules, skills, agents, mcp.json).
- FR-8.4: Global configuration (`~/.brainxio/settings.json`) merges correctly with project-level overrides.

### 5.9 Tooling & Developer Experience

- FR-9.1: Project builds and installs cleanly using only `uv` (no `pip --break-system-packages`).
- FR-9.2: All core commands are available via the `ai` (or `brainxio`) CLI entry point.
- FR-9.3: Test suite (pytest) passes with ≥ 70% coverage on core modules.
- FR-9.4: `ai --help` and `ai <command> --help` are clear and complete.

## 6. Technology Requirements

| Layer | Technology | Constraint |
|---|---|---|
| Core Runtime | Python 3.12+ with `uv` | `uv` only; no pip |
| JS Layer | Node 20+ with npm/pnpm | For browser automation / web UI |
| LLM Client | Ollama (Python + JS clients) | Official client; tool calling + structured outputs |
| Testing | pytest + Vitest + Playwright | TDD required |
| Async | asyncio + anyio | Clean concurrency |
| Configuration | Pydantic Settings + JSON | Type-safe, validated |
| Plugin System | importlib + entry points | Standard Python packaging |
| Event Bus | Simple typed event emitter | Lightweight, observable |

## 7. CLI Commands

| Command | Description |
|---|---|
| `ai brain <prompt>` | Run full PPAC decision loop |
| `ai status --extended` | Live brain state, RPE, context usage |
| `ai compile` | Build knowledge base from daily logs |
| `ai query <question>` | Semantic search over knowledge |
| `ai flush` | Process session memory |
| `ai introspect` | Self-reflection on learning patterns |
| `ai mcp list` | Show available MCP tools |
| `ai permissions check ...` | Test permission decisions |

## 8. Non-Goals

- Full self-fine-tuning loop (trainer node integration) — deferred to v0.2
- Production-grade eyes / voice plugins — basic stubs are acceptable
- Multi-user / multi-tenant support
- GUI installer or one-click setup

## 9. Dependencies

- `pydantic` — configuration and data models
- `click` or `typer` — CLI framework
- `ollama` — Ollama Python client
- `pytest`, `pytest-cov` — testing
- `ruff` — linting and formatting
- `psutil` — system metrics
- `rich` — terminal output and statusline

## 10. Success Criteria

A release candidate for v0.1 is ready only when:

1. All items in sections 1–7 of `docs/BASELINE.md` are marked complete and have passing automated tests.
2. A clean end-to-end session works:
   - `ai hook session-start`
   - Multiple `ai brain` decisions with tool use and RPE
   - `ai hook session-end`
   - `ai flush`
   - `ai compile`
   - `ai status --extended` shows correct state
3. At least one MCP-powered extension (e.g., browser automation via Puppeteer) works end-to-end.
4. Documentation (`BASELINE.md` + `ARCHITECTURE.md` + `HOOKS.md` + `PERMISSIONS.md`) is consistent and up to date.
5. The autonomous development loop (Claude-agent-sdk + MCP servers) can successfully implement a new small feature with zero human code changes after the initial prompt.

## 11. Timeline

| Phase | Duration | Deliverable |
|---|---|---|
| Phase 0 — Foundation | 2–3 weeks | Skeleton, Ollama client, PPAC stub, `~/.brainxio/` loader |
| Phase 1 — Brain Regions & Monitoring | 3–5 weeks | Full PPAC, RPE, metrics, statusline, baseline green |
| Phase 2 — Knowledge, Hooks, Permissions | 4–6 weeks | Full knowledge pipeline, mature permissions, plugins |
| Phase 3 — Release Preparation | 2 weeks | Clean git, public repo, first alpha release |

---

*This document is the contract between human developers and any autonomous agent working on the project. No feature work should begin until its acceptance criteria are defined here or in a linked test file.*
