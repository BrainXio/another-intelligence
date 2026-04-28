---
title: "v0.1 Success Criteria"
version: "0.1"
status: draft
updated: "2026-04-28"
---

# BASELINE.md — v0.1 Success Criteria

## Purpose

This document defines the **measurable baseline** that must be achieved before Another-Intelligence is considered ready for the first public alpha (v0.1). It serves as the contract between human developers and any autonomous agent (Claude-agent-sdk or future self-hosted version) working on the project.

All work is considered incomplete until every item in this document passes its acceptance test.

---

## 1. Functional Baseline

### 1.1 PPAC Decision Loop
- [ ] All five brain regions (Strategist, Executor, Reflex, and the two supporting stages) execute in **strict serial order** for every `decide()` call.
- [ ] The loop completes successfully on **at least 10 diverse test prompts** covering:
  - Simple factual queries
  - Multi-step planning
  - Tool-using tasks
  - Multi-turn conversations (minimum 5 turns)
  - Creative / open-ended prompts
- [ ] Context key consistency is enforced: the key used in `propose()` must match the key used in `record_outcome()`.

### 1.2 Brain Regions
- [ ] **Strategist** (PFC) produces structured proposals with multi-attribute expected values.
- [ ] **Executor** (Limbic + Basal Ganglia) correctly assigns emotional valence and performs Go/NoGo selection.
- [ ] **Reflex** (Parietal + Dopamine) performs noisy evidence accumulation and computes RPE.
- [ ] Each region emits a `BrainRegionActivated` event with correct metadata (region name, timestamp, input summary, output summary).

### 1.3 Outcome Recording & Learning
- [ ] Real external outcomes (test results, user feedback, system metrics) are captured and used to compute `RPE = actual − expected`.
- [ ] When `|RPE| > 0.3`, a valid preference pair (chosen / rejected) is exported to `~/.brainxio/training_datasets/`.
- [ ] Memory-value index is updated correctly after every outcome.

---

## 2. Observability & Monitoring Baseline

- [ ] Real-time **context window usage** is tracked and exposed via API and statusline (accurate to ±5% of actual tokens used).
- [ ] **System metrics** (CPU, memory, model latency, tokens per second) are collected and displayed.
- [ ] **Activity state machine** correctly reflects current phase (Idle, Proposing, Accumulating, Selecting, Learning, etc.).
- [ ] Event log (`~/.brainxio/state/brain_activity.jsonl`) is append-only and contains every major event.
- [ ] `ai status --extended` shows live brain state, latest RPE, active regions, and context usage.

---

## 3. Security & Permissions Baseline

- [ ] Capability-based permissions engine is implemented and active.
- [ ] Default policy is **least privilege** (new tools/MCP servers start with zero permissions).
- [ ] `settings.json` supports declarative allow / ask / deny rules per tool and per capability.
- [ ] PreToolUse hooks can influence permission decisions but **cannot bypass** an explicit deny rule.
- [ ] All permission decisions are logged with full context (who, what, why, outcome).

---

## 4. Hook System Baseline

- [ ] Typed event system supports at minimum:
  - `SessionStart`
  - `SessionEnd`
  - `PreToolUse`
  - `PostToolUse`
  - `BrainRegionActivated`
  - `RPEUpdated`
  - `MCPToolCalled`
- [ ] Hooks can be registered via `~/.brainxio/settings.json` or project `.brainxio/settings.json`.
- [ ] Hooks can be implemented as:
  - Shell commands
  - Python callables (entry points)
  - MCP tools
- [ ] Hook execution is observable and logged.

---

## 5. MCP (Model Context Protocol) Baseline

- [ ] Native MCP client is implemented in core.
- [ ] At least **3 MCP servers** are successfully registered and callable:
  1. Filesystem (read-only or scoped)
  2. One browser automation server (Puppeteer or Playwright)
  3. One additional server (Git, Memory, or custom test server)
- [ ] MCP tools appear to the model identically to native tools.
- [ ] MCP tool calls go through the full Permissions + Hook pipeline.
- [ ] `mcp.json` configuration is supported for both global (`~/.brainxio/`) and project (`.brainxio/`) scope.

---

## 6. Knowledge & Configuration Baseline

- [ ] `ai compile` successfully parses daily logs and produces structured articles.
- [ ] `ai query` returns relevant results from the compiled knowledge base.
- [ ] `~/.brainxio/` and `.brainxio/` directory structure is fully functional (settings, rules, skills, agents, mcp.json).
- [ ] Global configuration (`~/.brainxio/settings.json`) merges correctly with project-level overrides.

---

## 7. Tooling & Developer Experience Baseline

- [ ] Project builds and installs cleanly using only `uv` (no `pip --break-system-packages`).
- [ ] All core commands are available via the `ai` (or `brainxio`) CLI entry point.
- [ ] Test suite (pytest) passes with ≥ 70% coverage on core modules.
- [ ] `ai --help` and `ai <command> --help` are clear and complete.

---

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
4. Documentation (this file + ARCHITECTURE.md + HOOKS.md + PERMISSIONS.md) is consistent and up to date.
5. The autonomous development loop (Claude-agent-sdk + MCP servers) can successfully implement a new small feature with zero human code changes after the initial prompt.

---

## 9. Non-Goals for v0.1

- Full self-fine-tuning loop (trainer node integration) — deferred to v0.2
- Production-grade eyes / voice plugins — basic stubs are acceptable
- Multi-user / multi-tenant support
- GUI installer or one-click setup

---

**This document is the contract.**  
No feature work should begin on a module until its acceptance criteria are defined here or in a linked test file.
