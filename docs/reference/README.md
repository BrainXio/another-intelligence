# Reference

## Entry Points

| Name | Module | Description |
|------|--------|-------------|
| `ai` | `another_intelligence.cli:main` | Main CLI for brain decisions, hooks, status, and knowledge ops |

## CLI Commands

| Command | Description | Status |
|---------|-------------|--------|
| `ai brain decide` | Run the PPAC decision loop | Implemented |
| `ai brain regions` | Show recent brain region activations | Implemented |
| `ai hook session-start` | Start a session and emit event | Implemented |
| `ai hook session-end` | End a session and emit event | Implemented |
| `ai flush` | Clear persisted state and event log | Implemented |
| `ai compile` | Compile knowledge (stub) | Stub |
| `ai status` | Show current brain state | Implemented |
| `ai status --extended` | Show state + full event history | Implemented |
| `ai permissions check` | Evaluate a capability against policy | Implemented |
