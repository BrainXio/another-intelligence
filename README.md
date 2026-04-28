______________________________________________________________________

## title: "Another-Intelligence" version: "0.1" status: draft updated: "2026-04-28"

# README.md — Another-Intelligence

**A persistent neuroscience-grounded digital brain**

______________________________________________________________________

## What is Another-Intelligence?

**Another-Intelligence** (Cerebro) is a fully independent, Ollama-native cognitive architecture that thinks and learns like a biological brain.

It implements a strict **PPAC loop** (Proposer → Predictor → Accumulator → Actor → Critic) across three permanent roles:

- **Cerebro Strategist** — Prefrontal Cortex (planning & value computation)
- **Cerebro Executor** — Limbic + Basal Ganglia (emotional tagging & action selection)
- **Cerebro Reflex** — Parietal + Dopamine (evidence accumulation & RPE learning)

Every decision produces real **reward prediction error (RPE)** that drives continuous self-improvement through synthetic preference datasets and future QLoRA fine-tuning.

______________________________________________________________________

## Key Features

- **100% Ollama** — Runs on Max, Pro, Free, or local GPU tiers under the unified `Another-Intelligence/*` namespace.
- **MCP-Native** — First-class support for Model Context Protocol (filesystem, browser, git, memory, hardware, etc.).
- **Permissions-First** — Capability-based security with least-privilege defaults.
- **Typed Hook System** — Extensible lifecycle events (SessionStart, PreToolUse, RPEUpdated, …).
- **Observable Brain** — Real-time statusline + pluggable animated eyes.
- **Knowledge Pipeline** — Daily logs → structured articles → semantic query.
- **Plugin Architecture** — Easy to add voice, hardware, new displays, etc.
- **Autonomous Development Ready** — Designed for heavy use with Claude-agent-sdk + MCP servers.

______________________________________________________________________

## Quick Start

```bash
# Clone the project
git clone https://github.com/brainxio/another-intelligence.git
cd another-intelligence

# Setup Python environment
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# (Optional) Setup JavaScript layer
npm install

# Pull recommended models
ollama pull qwen3.5:14b
# Create your Cerebro models (see docs/ for ModelFiles)

# Run a first decision
ai brain "Explain how the PPAC loop works in simple terms"
```

______________________________________________________________________

## Core Commands

| Command                    | Description                          |
| -------------------------- | ------------------------------------ |
| `ai brain <prompt>`        | Run full PPAC decision loop          |
| `ai status --extended`     | Live brain state, RPE, context usage |
| `ai compile`               | Build knowledge base from daily logs |
| `ai query <question>`      | Semantic search over knowledge       |
| `ai flush`                 | Process session memory               |
| `ai introspect`            | Self-reflection on learning patterns |
| `ai mcp list`              | Show available MCP tools             |
| `ai permissions check ...` | Test permission decisions            |

______________________________________________________________________

## Project Structure

```
another-intelligence/
├── docs/                      # All architecture & guides (start here)
├── src/another_intelligence/  # Core Python package
├── plugins/                   # Example & core plugins
├── tests/
├── ~/.brainxio/               # Global config, rules, skills, memory
└── .brainxio/                 # Project-specific config (committed)
```

______________________________________________________________________

## Documentation Index

- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** — High-level design
- **[BASELINE.md](docs/BASELINE.md)** — v0.1 success criteria
- **[DEVELOPMENT.md](docs/DEVELOPMENT.md)** — Workflow & tooling
- **[HOOKS.md](docs/HOOKS.md)** — Hook system
- **[MCP.md](docs/MCP.md)** — Model Context Protocol
- **[PERMISSIONS.md](docs/PERMISSIONS.md)** — Security model
- **[PROMPTING.md](docs/PROMPTING.md)** — Rules & skills system
- **[PLUGIN-DEVELOPMENT.md](docs/PLUGIN-DEVELOPMENT.md)** — How to extend

______________________________________________________________________

## Philosophy

- Neuroscience fidelity over hype
- Independence over vendor lock-in
- Modularity and clarity over convenience
- Real learning (RPE) over stateless prompting
- Security and observability by default

______________________________________________________________________

## Status

**Current Phase:** Foundation & v0.1 Baseline\
**License:** Apache 2.0\
**Chat with us:** Use `ai brain` once installed.

______________________________________________________________________

**Made with ❤️ for genuine persistent cognition.**

*“Not simulating intelligence — building one.”*
