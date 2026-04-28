______________________________________________________________________

## title: "Another-Intelligence Reference Registry" version: "0.1" status: draft updated: "2026-04-28"

# Reference Registry

Central registry of all architectural components, entry points, and CI stages.

______________________________________________________________________

## Skills

| Skill | Purpose | Status |
|-------|---------|--------|
| `ai brain` | Run full PPAC decision loop | Planned |
| `ai status` | Show live brain state | Planned |
| `ai compile` | Build knowledge base | Planned |
| `ai query` | Semantic search | Planned |
| `ai flush` | Process session memory | Planned |
| `ai introspect` | Self-reflection | Planned |
| `ai mcp` | MCP server management | Planned |
| `ai permissions` | Permission testing | Planned |

______________________________________________________________________

## Agents

| Agent | Purpose | Status |
|-------|---------|--------|
| Strategist | Prefrontal Cortex planning | Planned |
| Executor | Limbic + Basal Ganglia selection | Planned |
| Reflex | Parietal + Dopamine accumulation | Planned |

______________________________________________________________________

## Hooks

| Hook | Event | Status |
|------|-------|--------|
| `SessionStart` | `SessionStart` | Planned |
| `SessionEnd` | `SessionEnd` | Planned |
| `PreToolUse` | `PreToolUse` | Planned |
| `PostToolUse` | `PostToolUse` | Planned |
| `BrainRegionActivated` | `BrainRegionActivated` | Planned |
| `RPEUpdated` | `RPEUpdated` | Planned |
| `ContextWindowChanged` | `ContextWindowChanged` | Planned |
| `PermissionRequested` | `PermissionRequested` | Planned |
| `MCPToolCalled` | `MCPToolCalled` | Planned |

______________________________________________________________________

## Entry Points

| Entry Point | Module | Purpose | Status |
|-------------|--------|---------|--------|
| `ai` | `another_intelligence.cli:main` | CLI entry point | Planned |

______________________________________________________________________

## Core Modules

| Module | Purpose | Status |
|--------|---------|--------|
| `brain` | DigitalBrain orchestrator + PPAC loop | Done |
| `events` | Typed event bus | Done |
| `state` | Activity state machine | Done |
| `context` | Context window tracker | Done |
| `permissions/engine` | Capability-based permissions | Done |
| `models/client` | Ollama client wrapper | Done |
| `models/resolver` | Tiered model resolver | Done |
| `mcp/client` | MCP client + registry + transport | Done |

______________________________________________________________________

## CI Pipeline Stages

| Stage | Command | Status |
|-------|---------|--------|
| Lint | `ruff check .` | Done |
| Format | `ruff format --check .` | Done |
| Test | `pytest -q` | Done |
| Coverage | `pytest --cov` | Done |

______________________________________________________________________

**End of Reference Registry**

*This document is updated alongside every feature PR. See `docs/doc-sync.md` for rules.*
