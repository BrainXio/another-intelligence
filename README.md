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

Every decision produces real RPE that updates a persistent memory-value index. Over time, Cerebro gets better at predicting which actions will succeed — not because it was fine-tuned on a static dataset, but because it learned from its own outcomes. The superpowers this externalizes:

- **Persistent memory** — Knowledge survives across sessions. Daily logs compile into structured articles that feed semantic query.
- **Real learning** — RPE updates a memory-value index continuously. Preference pair datasets are exported for future QLoRA fine-tuning.
- **MCP-native tooling** — All external tools (filesystem, browser, git, memory, hardware) route through a first-class MCP client. Any compliant MCP server works out of the box.
- **Neuroscience fidelity** — Every component maps to a biological mechanism. The architecture is grounded in the cognitive neuroscience of decision-making, not prompt engineering.

## What This Is

Another Intelligence is a persistent agent that hosts the PPAC loop and discovers external tools exclusively through MCP. It is the cognitive core of the BrainXio ecosystem — the thing that thinks, decides, and learns. The three discipline packages (ADHD, OCD, ASD) expose MCP servers that Cerebro discovers at runtime. No package imports another. Discovery and communication happen exclusively through the MCP registry.

## Core Architecture

### PPAC Loop Stages

Every decision flows through a strict serial pipeline:

1. **Strategist** (PFC) — proposes options, computes expected value
2. **Executor** (Limbic + Basal Ganglia) — emotional tagging + Go/NoGo action selection
3. **Reflex** (Parietal + Dopamine) — noisy evidence accumulation + RPE computation
4. **Outcome Recording** — real external feedback drives learning
5. **Learning** — memory-value index update + preference dataset generation

### Model Roles

Three Ollama model roles under the `Another-Intelligence/*` namespace:

| Role       | Brain Region                      | Purpose                                                          |
| ---------- | --------------------------------- | ---------------------------------------------------------------- |
| Strategist | Prefrontal Cortex (PFC/DLPFC-OFC) | Multi-attribute option evaluation and expected value computation |
| Executor   | Limbic System + Basal Ganglia     | Emotional valence tagging and Go/NoGo action selection           |
| Reflex     | Parietal LIP + Dopamine           | Noisy evidence accumulation and RPE encoding                     |

### MCP Client

External tools are discovered and called through a first-class MCP client:

| Server | Neuro Superpower            | Relationship                                           |
| ------ | --------------------------- | ------------------------------------------------------ |
| ADHD   | Coordination nervous system | Multi-agent message bus for parallel worktree sessions |
| ASD    | Systematizing memory        | Knowledge base compilation and semantic storage        |
| OCD    | Discipline & enforcement    | Rules, gates, modes, and standard enforcement          |

## Installation

```bash
# Clone the repo
git clone git@github.com:BrainXio/Another-Intelligence.git
cd another-intelligence

# Install with dev dependencies
uv sync
uv pip install -e ".[dev]"
```

## Usage

```bash
# Run a full PPAC decision
ai brain "Should I add caching to the API layer?"

# Show live brain state, RPE, and context usage
ai status --extended

# List available MCP tools and their servers
ai mcp list

# Check a permission decision
ai permissions check "filesystem.write" --config .brainxio/permissions.json
```

## Configuration Location

Cerebro reads configuration from two directories, mirroring the `.claude` model:

| Location       | Scope                        | Purpose                                               |
| -------------- | ---------------------------- | ----------------------------------------------------- |
| `~/.brainxio/` | Global (all projects)        | Rules, skills, agents, memory, MCP server registry    |
| `.brainxio/`   | Project-specific (committed) | Permissions, project-scoped MCP servers, hooks config |

### Environment Variables

| Variable          | Purpose                                                           |
| ----------------- | ----------------------------------------------------------------- |
| `AI_CONFIG_PATH`  | Override config directory (default: `~/.brainxio`)                |
| `AI_MODEL_PREFIX` | Override Ollama model namespace (default: `Another-Intelligence`) |

## Design Philosophy

**Neuroscience fidelity over hype.** Every component maps to a biological mechanism. The architecture is grounded in cognitive neuroscience (Shadlen, Frank, Schultz models), not prompt engineering trends.

**Independence over vendor lock-in.** Runs 100% on Ollama. No proprietary SDK dependency. The three model roles are open-weight models you control.

**Real learning over stateless prompting.** RPE = actual − expected. The memory-value index improves continuously from real outcomes. This is learning, not context-stuffing.
