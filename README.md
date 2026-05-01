# Another Intelligence — Cerebro

> **Another Intelligence** (Cerebro) is the cognitive core of the BrainXio ecosystem — a persistent, neuroscience-grounded digital brain that thinks and learns like a biological brain.
>
> It runs 100% on Ollama under three permanent model roles, hosts first-class MCP clients for all external tools, and improves continuously through real reward prediction error (RPE) learning.

## The Cerebro Parallel

Biological brains don't run prompts. They run a strict serial loop: the prefrontal cortex proposes options, the limbic system tags them with emotional valence, the parietal cortex accumulates noisy evidence toward a decision threshold, the basal ganglia select an action through Go/NoGo gating, and dopamine encodes the reward prediction error — actual minus expected — that drives learning.

That's the PPAC loop. And that's what Cerebro implements:

- **Proposer (PFC/DLPFC-OFC)**: Generates candidate plans and computes multi-attribute expected value for each option
- **Predictor (Limbic)**: Amygdala tags options with emotional valence (approach/avoid); hippocampus retrieves episodic memories for outcome prediction
- **Accumulator (Parietal LIP)**: Gradual, noisy evidence accumulation toward a decision threshold — the Shadlen model of perceptual decision-making
- **Actor (Basal Ganglia)**: Direct pathway (Go/D1) and indirect pathway (NoGo/D2) gate action selection — the Frank model of corticostriatal control
- **Critic (Dopamine)**: Encodes RPE = actual − expected; positive RPE strengthens Go for the chosen action; negative RPE strengthens NoGo — the Schultz model of dopaminergic learning

Every decision produces real RPE that updates a persistent memory-value index. Over time, Cerebro gets better at predicting which actions will succeed — not because it was fine-tuned on a static dataset, but because it learned from its own outcomes.

## Superpowers

The PPAC loop externalizes four cognitive superpowers that biological brains already have but digital systems consistently lack:

- **Persistent memory** — Knowledge survives across sessions. Daily logs compile into structured articles that feed semantic query. No context window limits, no forgetting between sessions.
- **Real learning** — RPE updates a memory-value index continuously. Every decision outcome strengthens or weakens the pathways that produced it. Preference pair datasets are exported for future QLoRA fine-tuning.
- **MCP-native tooling** — All external tools (filesystem, browser, git, memory, hardware) route through a first-class MCP client. Any compliant MCP server works out of the box. No vendor lock-in, no proprietary SDK.
- **Neuroscience fidelity** — Every component maps to a biological mechanism grounded in the cognitive neuroscience literature (Shadlen, Frank, Schultz models). This isn't prompt engineering — it's computational psychiatry.

## Quick Start

```bash
# Clone and install
git clone git@github.com:BrainXio/Another-Intelligence.git
cd another-intelligence
uv sync
uv pip install -e ".[dev]"

# Run a full PPAC decision
ai brain "Should I add caching to the API layer?"

# Show live brain state, RPE, and context usage
ai status --extended

# List available MCP tools and their servers
ai mcp list
```

Requires [Ollama](https://ollama.ai) with three model roles under the `Another-Intelligence/*` namespace. See `docs/DEVELOPMENT.md` for detailed setup.

## Architecture

### PPAC Loop Stages

Every decision flows through a strict serial pipeline:

1. **Strategist** (PFC) — proposes options, computes expected value
2. **Executor** (Limbic + Basal Ganglia) — emotional tagging + Go/NoGo action selection
3. **Reflex** (Parietal + Dopamine) — noisy evidence accumulation + RPE computation
4. **Outcome Recording** — real external feedback drives learning
5. **Learning** — memory-value index update + preference dataset generation

### Component Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Another-Intelligence                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐    │
│   │   DigitalBrain   │────▶│   PPAC Loop      │────▶│   5 Brain Regions│    │
│   │   (Orchestrator) │     │   (Strict Serial)│     │   (Strategist,   │    │
│   └──────────────────┘     └──────────────────┘     │    Executor,     │    │
│                                                     │    Reflex)       │    │
│   ┌──────────────────┐     ┌──────────────────┐     └──────────────────┘    │
│   │   Permissions    │◀────│   Hook System    │                             │
│   │   Engine         │     │   (Typed Events) │                             │
│   └──────────────────┘     └──────────────────┘                             │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                        MCP Client (Core)                            │   │
│   │  • Puppeteer / Playwright  • Filesystem  • Git  • Memory  • Custom  │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│   ┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐    │
│   │   Knowledge      │     │   RPE + Memory   │     │   Plugin Loader  │    │
│   │   Pipeline       │     │   Value Index    │     │   (Core + Ext)   │    │
│   └──────────────────┘     └──────────────────┘     └──────────────────┘    │
│                                                                             │
│   Configuration: ~/.brainxio/  +  .brainxio/ (project)                      │
│   Models: Another-Intelligence/strategist, /executor, /reflex (tiered)      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Model Roles

Three Ollama model roles under the `Another-Intelligence/*` namespace:

| Role       | Brain Region                      | Purpose                                                          |
| ---------- | --------------------------------- | ---------------------------------------------------------------- |
| Strategist | Prefrontal Cortex (PFC/DLPFC-OFC) | Multi-attribute option evaluation and expected value computation |
| Executor   | Limbic System + Basal Ganglia     | Emotional valence tagging and Go/NoGo action selection           |
| Reflex     | Parietal LIP + Dopamine           | Noisy evidence accumulation and RPE encoding                     |

### Configuration

Cerebro reads configuration from two directories, mirroring the `.claude` model:

| Location       | Scope                        | Purpose                                               |
| -------------- | ---------------------------- | ----------------------------------------------------- |
| `~/.brainxio/` | Global (all projects)        | Rules, skills, agents, memory, MCP server registry    |
| `.brainxio/`   | Project-specific (committed) | Permissions, project-scoped MCP servers, hooks config |

## MCP Integration

Cerebro discovers and calls external tools exclusively through its first-class MCP client. No package imports another — discovery and communication happen at runtime through the MCP registry.

| Server | Neuro Superpower            | Role                                            |
| ------ | --------------------------- | ----------------------------------------------- |
| ADHD   | Coordination nervous system | Multi-agent message bus for parallel worktrees  |
| ASD    | Systematizing memory        | Knowledge base compilation and semantic storage |
| OCD    | Discipline & enforcement    | Quality gates, standards, modes, and linting    |

If any MCP server is unavailable, Cerebro degrades gracefully: no OCD means manual standards checks, no ASD means ephemeral knowledge, no ADHD means solo operation.

## Persistent Memory & RPE Learning

### Knowledge Pipeline

Raw daily logs (`USER/logs/daily/`) are compiled by ASD into structured, versioned knowledge artifacts (`USER/kb/`) with YAML frontmatter, typed categories (concept, mechanism, outcome, reference, connection), cross-references, and TF-IDF semantic search.

### RPE Learning Loop

Every decision produces a reward prediction error — the difference between expected and actual outcome. This RPE updates a persistent memory-value index:

- **Positive RPE** (outcome exceeded expectations → dopamine burst): Strengthens Go pathways for the chosen action
- **Negative RPE** (outcome fell short → dopamine dip): Strengthens NoGo pathways, suppressing the chosen action

Over time, this creates a self-improving system that learns from its own outcomes without requiring fine-tuning on static datasets.

## Development & Contribution

```bash
# Setup dev environment
uv sync
uv pip install -e ".[dev]"

# Run tests
uv run pytest -q
uv run pytest --cov=src/another_intelligence --cov-report=term-missing

# Lint & format
uv run ruff check .
uv run ruff format --check .

# CLI
ai --help
ai brain "prompt"
ai status --extended
```

**Contribution guidelines**: See `CONTRIBUTING.md` for branch naming, conventional commits, PR workflow, and code style. All development must happen in worktrees — never edit directly on `main`.

**Key documents** in `docs/`:

- `ARCHITECTURE.md` — Full system design and component reference
- `BASELINE.md` — v0.1 acceptance criteria
- `DEVELOPMENT.md` — Workflow and environment setup
- `PERMISSIONS.md` — Capability-based permission system
- `HOOKS.md` — Typed lifecycle events
- `MCP.md` — MCP client protocol and server registration

## Related Repos & Roadmap

### Ecosystem

| Package  | Directory                                 | Role                                                    | Type       |
| -------- | ----------------------------------------- | ------------------------------------------------------- | ---------- |
| **ADHD** | `attention-deficit-hyperactivity-driver/` | Coordination nervous system — multi-agent message bus   | MCP Server |
| **ASD**  | `autism-spectrum-driver/`                 | Systematizing memory — KB compilation, semantic storage | MCP Server |
| **OCD**  | `obsessive-compulsive-driver/`            | Discipline & enforcement — rules, gates, modes          | MCP Server |

### v0.1 Roadmap (Current)

- [x] Architecture docs and acceptance criteria
- [ ] Core PPAC loop implementation (Strategist, Executor, Reflex)
- [ ] Permissions engine with capability-based checks
- [ ] Hook system with typed lifecycle events
- [ ] MCP client with auto-discovery
- [ ] Knowledge pipeline integration with ASD
- [ ] RPE learning with memory-value index
- [ ] CLI with brain, status, and mcp subcommands

See `docs/BASELINE.md` for the complete acceptance criteria.

## License

Apache-2.0. See `LICENSE`.
