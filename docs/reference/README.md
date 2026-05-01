## \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_--- title: "Project Reference" aliases: ["Reference"] tags: [reference, docs] created: 2026-04-28 updated: 2026-05-01

# Reference

## Entry Points

| Name | Module                          | Description                                                    |
| ---- | ------------------------------- | -------------------------------------------------------------- |
| `ai` | `another_intelligence.cli:main` | Main CLI for brain decisions, hooks, status, and knowledge ops |

## Core Modules

| Module                                    | Description                              |
| ----------------------------------------- | ---------------------------------------- |
| `another_intelligence.brain`              | DigitalBrain orchestrator with PPAC loop |
| `another_intelligence.events`             | Typed event bus                          |
| `another_intelligence.state`              | Activity phase state machine             |
| `another_intelligence.context`            | Context window tracker                   |
| `another_intelligence.strategist`         | PFC option proposer                      |
| `another_intelligence.executor`           | Limbic + Basal Ganglia evaluator         |
| `another_intelligence.reflex`             | Parietal evidence accumulator            |
| `another_intelligence.rpe`                | Reward Prediction Error engine           |
| `another_intelligence.rpe.telemetry`      | Structured JSONL telemetry for PPAC      |
| `another_intelligence.memory.value_index` | Learned memory-value index               |
| `another_intelligence.models.client`      | Ollama client wrapper                    |
| `another_intelligence.models.resolver`    | Tiered model resolver                    |
| `another_intelligence.permissions.engine` | Capability-based permissions engine      |
| `another_intelligence.hooks.registry`     | Hook registration and discovery          |
| `another_intelligence.hooks.runner`       | Hook execution engine                    |
| `another_intelligence.knowledge.compiler` | Daily log → structured articles          |
| `another_intelligence.knowledge.query`    | Knowledge base search                    |
| `another_intelligence.mcp.client`         | MCP client + registry + transport        |
| `another_intelligence.metrics`            | Metrics collection and event logging     |
| `another_intelligence.statusline`         | Live brain state renderer                |

## Declarative Permissions Format

`settings.json` supports human-friendly allow / ask / deny / escalation rules:

```json
{
  "permissions": {
    "allow": ["mcp.fs.read", "mcp.memory.*"],
    "ask": ["mcp.fs.write"],
    "deny": ["mcp.fs.delete"],
    "escalation": ["mcp.*.delete"]
  }
}
```

- `allow` — capabilities granted without confirmation
- `ask` — capabilities requiring confirmation
- `deny` — explicit deny rules (checked before grants)
- `escalation` — promotes allow to ask for high-impact operations

## CLI Commands

| Command                         | Description                            | Status      |
| ------------------------------- | -------------------------------------- | ----------- |
| `ai brain decide`               | Run the PPAC decision loop             | Implemented |
| `ai brain regions`              | Show recent brain region activations   | Implemented |
| `ai hook session-start`         | Start a session and emit event         | Implemented |
| `ai hook session-end`           | End a session and emit event           | Implemented |
| `ai flush`                      | Clear persisted state and event log    | Implemented |
| `ai compile`                    | Compile knowledge from daily logs      | Implemented |
| `ai query`                      | Search the compiled knowledge base     | Implemented |
| `ai status`                     | Show current brain state               | Implemented |
| `ai status --extended`          | Show state + full event history        | Implemented |
| `ai permissions check`          | Evaluate a capability against policy   | Implemented |
| `ai permissions check --config` | Evaluate with custom settings.json     | Implemented |
| `ai rpe analyze`                | Analyze telemetry and show RPE metrics | Implemented |
| `ai rpe analyze --since`        | Filter analysis by date range          | Implemented |
| `ai rpe analyze --region`       | Filter by decision option              | Implemented |
| `ai rpe export-pairs`           | Export QLoRA preference-pair dataset   | Implemented |
| `ai rpe record --outcome`       | Record external outcome for RPE loop   | Implemented |
| `ai rpe ingest`                 | Rank prototype shortlist by EV         | Implemented |
| `ai rpe ingest --from-mcp`      | Query ASD scanner via MCP              | Implemented |
| `ai rpe ingest --post-to-bus`   | Post ranked results to ADHD bus        | Implemented |
| `ai mcp status`                 | Show MCP server connection status      | Implemented |
| `ai mcp status --extended`      | Live health probe with tool counts     | Implemented |

## Exported Classes

| Class                    | Module                                    |
| ------------------------ | ----------------------------------------- |
| `DigitalBrain`           | `another_intelligence.brain`              |
| `BrainEvent`             | `another_intelligence.events`             |
| `StateMachine`           | `another_intelligence.state`              |
| `ContextWindow`          | `another_intelligence.context`            |
| `Strategist`             | `another_intelligence.strategist`         |
| `Proposal`               | `another_intelligence.strategist`         |
| `Executor`               | `another_intelligence.executor`           |
| `Evaluation`             | `another_intelligence.executor`           |
| `Reflex`                 | `another_intelligence.reflex`             |
| `Selection`              | `another_intelligence.reflex`             |
| `RPEEngine`              | `another_intelligence.rpe`                |
| `TelemetryRecord`        | `another_intelligence.rpe.telemetry`      |
| `TelemetryRecorder`      | `another_intelligence.rpe.telemetry`      |
| `TelemetryAnalyzer`      | `another_intelligence.rpe.telemetry`      |
| `MemoryValueIndex`       | `another_intelligence.memory`             |
| `PreferencePairExporter` | `another_intelligence.memory.pairs`       |
| `PermissionEngine`       | `another_intelligence.permissions.engine` |
| `PermissionDecision`     | `another_intelligence.permissions.engine` |
| `HookRegistry`           | `another_intelligence.hooks`              |
| `HookRunner`             | `another_intelligence.hooks`              |
| `HookConfig`             | `another_intelligence.hooks`              |
| `HookType`               | `another_intelligence.hooks`              |
| `HookResult`             | `another_intelligence.hooks`              |
| `KnowledgeCompiler`      | `another_intelligence.knowledge`          |
| `KnowledgeQuery`         | `another_intelligence.knowledge`          |
| `Article`                | `another_intelligence.knowledge`          |
| `MCPClient`              | `another_intelligence.mcp`                |
| `MCPRegistry`            | `another_intelligence.mcp`                |
| `StdioConnection`        | `another_intelligence.mcp`                |
| `MCPServerConfig`        | `another_intelligence.mcp`                |
| `MCPToolDefinition`      | `another_intelligence.mcp`                |
| `MetricsCollector`       | `another_intelligence.metrics`            |
| `StatuslineRenderer`     | `another_intelligence.statusline`         |
