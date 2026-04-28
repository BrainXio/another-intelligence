______________________________________________________________________

## title: "Development Planning" version: "0.1" status: draft updated: "2026-04-28"

# Planning — v0.1 Roadmap

______________________________________________________________________

## Done

### MCP Client

- [x] Native MCP client in core (`src/another_intelligence/mcp/client.py`)
- [x] Auto-discovery via `mcp.json`
- [x] Permissions + Hook pipeline integration
- [x] Tool caching per session
- [x] Stdio transport with JSON-RPC
- [x] Event emission (`PreToolUse`, `PostToolUse`, `MCPToolCalled`)
- [x] Full test suite (26 tests)

### Core Infrastructure

- [x] DigitalBrain orchestrator with strict serial PPAC loop
- [x] Typed event bus (`BrainRegionActivated`, `RPEUpdated`, etc.)
- [x] Activity state machine (`StateMachine`)
- [x] Context window tracker (`ContextWindow`)
- [x] Capability-based permissions engine
- [x] Ollama client wrapper + tiered model resolver

### CI & Tooling

- [x] pytest + coverage pipeline
- [x] Ruff lint + format
- [x] Pre-commit hooks

______________________________________________________________________

## Pending

### PPAC Decision Loop Completion

- [ ] End-to-end validation on 10 diverse prompts
- [ ] Context key consistency enforcement
- [ ] Preference dataset export when |RPE| > 0.3

### Observability

- [ ] Real-time context window tracking (±5% accuracy)
- [ ] System metrics collection (CPU, memory, latency)
- [ ] Activity state machine display
- [ ] `ai status --extended` command

### Hook System

- [ ] Hook registration via `settings.json`
- [ ] Shell command hooks
- [ ] Python callable hooks
- [ ] MCP tool hooks

### Knowledge Pipeline

- [ ] `ai compile` command
- [ ] `ai query` command
- [ ] `~/.brainxio/` directory structure

### MCP Ecosystem

- [ ] Filesystem server integration (live)
- [ ] Browser automation server integration (live)
- [ ] Git server integration (live)

### CLI & Commands

- [ ] All `ai <command>` implementations
- [ ] Help text completeness

______________________________________________________________________

**End of Planning**

*Update this document before creating any PR that ships a planned item.*
