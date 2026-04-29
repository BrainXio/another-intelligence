______________________________________________________________________

## title: "From Prototype to Clean Core" version: "0.1" status: draft updated: "2026-04-29"

# MIGRATION.md — From Prototype to Clean Core

## Purpose

This document explains the deliberate separation between the current Claude-infused prototype (`~/work/_meta`) and the new clean `another-intelligence` core (`~/work/projects/another-intelligence`). It serves as a reference only — **no code will be copied or directly refactored**.

______________________________________________________________________

## 1. Why a Clean Rewrite

- The existing prototype is heavily tied to Claude Code SDK, hooks, and Anthropic-specific patterns.
- We want full ownership: 100% Ollama-based, independent, and releasable as open source.
- A clean-slate approach ensures better architecture, testability, and long-term maintainability.
- The prototype remains valuable as **inspiration and concept validation**.

______________________________________________________________________

## 2. Mapping Table (Concepts Only)

| Prototype Concept                      | New Core Equivalent                                    | Migration Approach                     |
| -------------------------------------- | ------------------------------------------------------ | -------------------------------------- |
| PPAC Loop in `core/loop.py`            | `DigitalBrain.decide()` + strict PPAC                  | Re-implement from ARCHITECTURE.md spec |
| Cerebro Strategist / Executor / Reflex | Same names under `Another-Intelligence/*`              | New Ollama ModelFiles + agents         |
| RPE computation                        | `rpe/` subpackage + memory-value index                 | Fresh implementation with tests        |
| Animated eyes + statusline             | Plugin system + event-driven DisplayController         | Core events → plugins                  |
| Claude hooks (session-start etc.)      | Typed Hook System (HOOKS.md)                           | New registration & execution model     |
| Knowledge base compilation             | `ai compile` + structured articles                     | New pipeline using daily logs          |
| Model tier detection                   | `model_resolver.py` from ANTHROPIC_MODEL → generalized | Support Ollama tiers + env vars        |
| `~/.ai/` directory                     | `~/.brainxio/`                                         | New cleaner structure                  |
| Dev tracker / backlog                  | Built-in via RPE + SQLite                              | Integrated into core                   |
| Self-fine-tuning (Unsloth)             | RPE → dataset → trainer node (v0.2)                    | Deferred, dataset pipeline first       |

______________________________________________________________________

## 3. Non-Migration Rules

- **No direct file copying** from the prototype.
- **No import of prototype modules**.
- Concepts and user experience (CLI commands, eyes behavior, knowledge workflow) should feel continuous, but implementation must be new.
- The prototype can continue running in parallel during development for comparison.

______________________________________________________________________

## 4. Phase-by-Phase Migration Guidance

**Phase 0 (Foundation)**

- Create skeleton + core documents (done)
- Implement minimal Ollama client + PPAC stub

**Phase 1 (Brain Baseline)**

- 5-region PPAC working with real models
- Basic hooks, permissions, MCP

**Phase 2 (Feature Parity)**

- Knowledge pipeline, statusline, eyes (basic)
- Full CLI surface (`ai brain`, `ai status`, `ai compile`, etc.)

**Phase 3 (Release)**

- Clean git re-init + public repo
- Documentation complete
- First alpha release

______________________________________________________________________

## 5. What to Keep from Prototype (Inspiration Only)

- Neuroscience fidelity (PPAC + RPE mapping)
- Tiered model strategy (Max/Pro/Free/Local)
- Unified `Another-Intelligence/*` naming
- Event-driven status and eyes reactivity
- Daily log → knowledge compilation flow
- Self-improvement vision (RPE → QLoRA)

______________________________________________________________________

## 6. Success Criteria for Migration

The migration is considered successful when:

- The new core can run a full PPAC session with tool use, RPE learning, and knowledge persistence.
- User experience (CLI commands, configuration, output) feels like a natural evolution of the prototype.
- All baseline criteria in `BASELINE.md` are met.
- The old prototype can be archived or retired without loss of core functionality.

______________________________________________________________________

## 7. Timeline Expectation

- v0.1 Alpha: Feature parity with prototype’s core brain loop + MCP/hooks.
- v0.2: Eyes, voice, full self-improvement pipeline.
- v1.0: Production-ready, polished plugins, public release.

______________________________________________________________________

**This document prevents accidental tight coupling to the prototype.**\
It will be updated if new insights from the old codebase emerge during development.
