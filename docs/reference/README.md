______________________________________________________________________

## title: "Project Reference" aliases: ["Reference"] tags: [reference, docs] created: 2026-04-28 updated: 2026-04-28

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
| `another_intelligence.models.client`      | Ollama client wrapper                    |
| `another_intelligence.models.resolver`    | Tiered model resolver                    |
| `another_intelligence.permissions.engine` | Capability-based permissions engine      |
| `another_intelligence.knowledge.compiler` | Daily log → structured articles          |
| `another_intelligence.knowledge.query`    | Knowledge base search                    |
| `another_intelligence.mcp.client`         | MCP client + registry + transport        |

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

| Command                 | Description                          | Status      |
| ----------------------- | ------------------------------------ | ----------- |
| `ai brain decide`       | Run the PPAC decision loop           | Implemented |
| `ai brain regions`      | Show recent brain region activations | Implemented |
| `ai hook session-start` | Start a session and emit event       | Implemented |
| `ai hook session-end`   | End a session and emit event         | Implemented |
| `ai flush`              | Clear persisted state and event log  | Implemented |
| `ai compile`            | Compile knowledge from daily logs    | Implemented |
| `ai query`              | Search the compiled knowledge base   | Implemented |
| `ai status`             | Show current brain state             | Implemented |
| `ai status --extended`  | Show state + full event history      | Implemented |
| `ai permissions check`  | Evaluate a capability against policy | Implemented |
| `ai permissions check --config` | Evaluate with custom settings.json | Implemented |

## Exported Classes

| Class               | Module                                    |
| ------------------- | ----------------------------------------- |
| `DigitalBrain`      | `another_intelligence.brain`              |
| `BrainEvent`        | `another_intelligence.events`             |
| `StateMachine`      | `another_intelligence.state`              |
| `ContextWindow`     | `another_intelligence.context`            |
| `PermissionEngine`  | `another_intelligence.permissions.engine` |
| `KnowledgeCompiler` | `another_intelligence.knowledge.compiler` |
| `KnowledgeQuery`    | `another_intelligence.knowledge.query`    |
| `Article`           | `another_intelligence.knowledge.compiler` |
