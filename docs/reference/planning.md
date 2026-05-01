---
title: Project Planning
aliases: [Planning]
tags: [planning, roadmap]
created: '2026-04-28'
updated: '2026-05-01'
---

# Planning

## v0.1 Baseline Status

### Functional

- [x] DigitalBrain + strict 5-stage PPAC loop
- [x] Event-driven state machine
- [x] Ollama client wrapper + tiered model resolver
- [x] Capability-based permissions engine
- [x] Knowledge pipeline (`compile`, `query`)
- [x] MCP client
- [x] Hook system implementation
- [x] RPE learning + memory-value index
- [x] Plugin loader

### Observability

- [x] Context window tracking API
- [x] System metrics collection
- [x] Statusline renderer
- [x] Event log persistence

### Tooling

- [x] pytest suite with coverage gates
- [x] ruff linting
- [x] CI pipeline (GitHub Actions)
- [x] Full CLI command suite
- [x] Documentation sync automation

## Done

- Project skeleton + pyproject.toml
- Permissions engine + declarative rules
- Ollama client + resolver
- DigitalBrain orchestrator
- Knowledge compiler + query
- MCP client + registry + transport + integration tests
- Hook system (registry, runner, typed events)
- RPE engine + memory-value index + preference pair export
- Statusline renderer + metrics collector
- Context window tracker
- Test suite restructured to mirror `src/` layout
- Multi-agent orchestration rules + scripts
