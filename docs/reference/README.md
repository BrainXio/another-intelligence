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
| `another_intelligence.mcp.client`         | MCP client + registry + transport        |

## CLI Commands

| Command                 | Description                          | Status      |
| ----------------------- | ------------------------------------ | ----------- |
| `ai brain decide`       | Run the PPAC decision loop           | Implemented |
| `ai brain regions`      | Show recent brain region activations | Implemented |
| `ai hook session-start` | Start a session and emit event       | Implemented |
| `ai hook session-end`   | End a session and emit event         | Implemented |
| `ai flush`              | Clear persisted state and event log  | Implemented |
| `ai compile`            | Compile knowledge (stub)             | Stub        |
| `ai status`             | Show current brain state             | Implemented |
| `ai status --extended`  | Show state + full event history      | Implemented |
| `ai permissions check`  | Evaluate a capability against policy | Implemented |
