---
title: "Another-Intelligence Development Roadmap"
version: "0.1"
status: draft
updated: "2026-04-28"
---

# ROADMAP.md — Another-Intelligence Development Roadmap

## Vision

Reach a stable, self-improving, neuroscience-faithful digital brain by the end of 2026 that can run fully autonomously on Ollama infrastructure while supporting rich plugin and MCP ecosystems.

---

## Release Phases

### v0.1 — Foundation & Baseline (Current Target)

**Goal:** Clean, testable core with full PPAC loop and essential systems.

**Key Deliverables**
- DigitalBrain + strict 5-stage PPAC
- Strategist / Executor / Reflex agents with Ollama
- Tiered model resolution (Max/Pro/Free/Local)
- Permissions engine + typed hook system
- Native MCP client with 3+ servers
- Basic knowledge pipeline (`compile`, `query`, `lint`)
- Context tracking + event-driven observability
- `ai` CLI with core commands
- Full test suite + autonomous development loop

**Success:** All items in `BASELINE.md` green.

**Timeline:** 3–5 weeks

---

### v0.2 — Observability & Self-Improvement

**Goal:** Make the brain visibly alive and learning.

**Key Deliverables**
- Pluggable eyes/display system (GTK + WebSocket)
- Real-time statusline
- Full RPE → preference dataset pipeline
- Basic self-reflection (`introspect`)
- Voice plugin (Piper TTS + Whisper/Vosk STT)
- Hardware plugin foundation
- Daily memory consolidation
- First QLoRA trainer node integration (manual trigger)

**Success:** Brain visibly reacts to decisions; RPE datasets are generated and usable.

**Timeline:** 4–6 weeks after v0.1

---

### v0.3 — Extensibility & Ecosystem

**Goal:** Make it easy for others to extend.

**Key Deliverables**
- Mature plugin system with hot-reload
- Official plugin registry + template
- Advanced MCP servers (Memory vector store, Serena, custom hardware)
- Skill system with marketplace-ready examples
- Multi-session support
- Improved prompting & rules engine
- Comprehensive documentation + examples

**Success:** External contributors can build and publish high-quality plugins.

**Timeline:** 5–7 weeks after v0.2

---

### v1.0 — Production & Self-Sustaining

**Goal:** A truly persistent, self-improving digital mind.

**Key Deliverables**
- Automated fine-tuning loop (RPE → dataset → Unsloth → hot-swap)
- Long-term episodic memory with consolidation
- Robust multi-tier fallback & resource optimization
- Security audit + formal verification of permission model
- Public release on GitHub + PyPI
- Contributor guide + governance model
- Performance benchmarks across hardware tiers

**Success:** Cerebro can run continuously for weeks, visibly improve its own decision quality, and support real-world workloads.

**Timeline:** Q4 2026

---

## Future Horizons (v1.x+)

- Distributed brain nodes (multi-device cognition)
- Vision integration (VLM + MCP camera)
- Embodied agents (robotics via hardware plugins)
- Community model fine-tunes repository
- Research mode with paper ingestion & hypothesis generation
- Persistent identity across years (lifelong memory)

---

## Current Priorities (as of 2026-04-28)

1. Complete Tier 1 documents + project skeleton
2. Implement minimal Ollama PPAC loop (target: end of this week)
3. Achieve v0.1 baseline
4. Hand off large implementation chunks to autonomous Claude-agent-sdk + MCP

---

## How to Influence the Roadmap

- Open issues on GitHub (once public)
- Submit plugins or MCP servers
- Contribute to `ROADMAP.md` via PR
- Use `ai brain` inside the repo to discuss features

---

**This roadmap is flexible and will evolve with real usage and community input.**  
All major changes will be reflected here and announced in `CHANGELOG.md`.

*Let’s build something that actually thinks.*