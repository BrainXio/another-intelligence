## \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_--- title: "v0.1 Success Criteria" version: "0.1" status: draft updated: "2026-05-01"

# BASELINE.md — v0.1 Success Criteria

## Purpose

This document defines the **measurable baseline** that must be achieved before Another-Intelligence is considered ready for the first public alpha (v0.1). It serves as the contract between human developers and any autonomous agent (Claude-agent-sdk or future self-hosted version) working on the project.

All work is considered incomplete until every item in this document passes its acceptance test.

______________________________________________________________________

## 1. Functional Baseline

### 1.1 PPAC Decision Loop

- [x] All five brain regions (Strategist, Executor, Reflex, and the two supporting stages) execute in **strict serial order** for every `decide()` call.
- [x] The loop completes successfully on **at least 10 diverse test prompts** covering:
  - Simple factual queries
  - Multi-step planning
  - Tool-using tasks
  - Multi-turn conversations (minimum 5 turns)
  - Creative / open-ended prompts
- [x] Context key consistency is enforced: the key used in `propose()` must match the key used in `record_outcome()`.

### 1.2 Brain Regions

- [x] **Strategist** (PFC) produces structured proposals with multi-attribute expected values.
- [x] **Executor** (Limbic + Basal Ganglia) correctly assigns emotional valence and performs Go/NoGo selection.
- [x] **Reflex** (Parietal + Dopamine) performs noisy evidence accumulation and computes RPE.
- [x] Each region emits a `BrainRegionActivated` event with correct metadata (region name, timestamp, input summary, output summary).

### 1.3 Outcome Recording & Learning

- [x] Real external outcomes (test results, user feedback, system metrics) are captured and used to compute `RPE = actual − expected`.
- [x] When `|RPE| > 0.3`, a valid preference pair (chosen / rejected) is exported to `~/.brainxio/training_datasets/`.
- [x] Memory-value index is updated correctly after every outcome.

______________________________________________________________________

## 2. Observability & Monitoring Baseline

- [x] Real-time **context window usage** is tracked and exposed via API and statusline.
- [x] **System metrics** (CPU, memory, model latency, tokens per second) are collected and displayed.
- [x] **Activity state machine** correctly reflects current phase (Idle, Proposing, Accumulating, Selecting, Learning, etc.).
- [x] Event log (`~/.brainxio/state/brain_activity.jsonl`) is append-only and contains every major event.
- [x] `ai status --extended` shows live brain state, latest RPE, active regions, and context usage.

______________________________________________________________________

## 3. Security & Permissions Baseline

- [x] Capability-based permissions engine is implemented and active.
- [x] Default policy is **least privilege** (new tools/MCP servers start with zero permissions).
- [x] `settings.json` supports declarative allow / ask / deny rules per tool and per capability.
- [x] PreToolUse hooks can influence permission decisions but **cannot bypass** an explicit deny rule.
- [x] All permission decisions are logged with full context (who, what, why, outcome).

______________________________________________________________________

## 4. Hook System Baseline

- [x] Typed event system supports at minimum:
  - `SessionStart`
  - `SessionEnd`
  - `PreToolUse`
  - `PostToolUse`
  - `BrainRegionActivated`
  - `RPEUpdated`
  - `MCPToolCalled`
- [x] Hooks can be registered via `~/.brainxio/settings.json` or project `.brainxio/settings.json`.
- [x] Hooks can be implemented as:
  - Shell commands
  - Python callables (entry points)
  - MCP tools
- [x] Hook execution is observable and logged.

______________________________________________________________________

## 5. MCP (Model Context Protocol) Baseline

- [x] Native MCP client is implemented in core.
- [x] At least **3 MCP servers** are successfully registered and callable (ADHD, OCD, ASD).
- [x] MCP tools appear to the model identically to native tools.
- [x] MCP tool calls go through the full Permissions + Hook pipeline.
- [x] `mcp.json` configuration is supported for both global (`~/.brainxio/`) and project (`.brainxio/`) scope.

______________________________________________________________________

## 6. Knowledge & Configuration Baseline

- [x] `ai compile` successfully parses daily logs and produces structured articles.
- [x] `ai query` returns relevant results from the compiled knowledge base.
- [x] `~/.brainxio/` and `.brainxio/` directory structure is fully functional (settings, rules, skills, agents, mcp.json).
- [x] Global configuration (`~/.brainxio/settings.json`) merges correctly with project-level overrides.

______________________________________________________________________

## 7. Tooling & Developer Experience Baseline

- [x] Project builds and installs cleanly using only `uv` (no `pip --break-system-packages`).
- [x] All core commands are available via the `ai` CLI entry point.
- [x] Test suite (pytest) passes with ≥ 70% coverage on core modules.
- [x] `ai --help` and `ai <command> --help` are clear and complete.

______________________________________________________________________

## 8. Definition of Done for v0.1 Baseline

A release candidate for v0.1 is ready **only when**:

1. All items in sections 1–7 above are marked complete and have passing automated tests.
2. A clean end-to-end session works:
   - `ai hook session-start`
   - Multiple `ai brain` decisions with tool use and RPE
   - `ai hook session-end`
   - `ai flush`
   - `ai compile`
   - `ai status --extended` shows correct state
3. At least one MCP-powered extension (e.g., browser automation via Puppeteer) works end-to-end.
4. [x] Documentation (this file + ARCHITECTURE.md + HOOKS.md + PERMISSIONS.md) is consistent and up to date.
5. The autonomous development loop (Claude-agent-sdk + MCP servers) can successfully implement a new small feature with zero human code changes after the initial prompt.

______________________________________________________________________

## 9. Non-Goals for v0.1

- Full self-fine-tuning loop (trainer node integration) — deferred to v0.2
- Production-grade eyes / voice plugins — basic stubs are acceptable
- Multi-user / multi-tenant support
- GUI installer or one-click setup

______________________________________________________________________

**This document is the contract.**\
No feature work should begin on a module until its acceptance criteria are defined here or in a linked test file.
