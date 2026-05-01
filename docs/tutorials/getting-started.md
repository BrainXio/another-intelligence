---
title: Getting Started with Another-Intelligence
aliases: [Getting Started, Quick Start]
tags: [tutorial, getting-started, setup]
created: '2026-05-01'
updated: '2026-05-01'
---

# Getting Started with Another-Intelligence

This tutorial walks you through installing Another-Intelligence (Cerebro), configuring it for your environment, and running your first PPAC decision loop.

## What You Will Learn

By the end of this tutorial, you will have:

1. Installed the package and dependencies
2. Configured your local Ollama models
3. Run a single PPAC decision via the CLI
4. Verified that all brain regions activated correctly

## Prerequisites

Before starting, ensure you have:

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) for Python package management
- [Ollama](https://ollama.com/) running locally
- Git

## Step 1: Install the Package

Clone the repository and set up the environment:

```bash
git clone https://github.com/brainxio/another-intelligence.git
cd another-intelligence
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

Verify the installation:

```bash
ai --help
```

## Step 2: Configure Ollama Models

Cerebro expects models under the `Another-Intelligence/*` namespace. For this tutorial, pull a lightweight local model:

```bash
ollama pull qwen3.5:14b
```

Then create a minimal model configuration in `~/.brainxio/models.json`:

```json
{
  "default": "qwen3.5:14b",
  "tiers": {
    "local": ["qwen3.5:14b"]
  }
}
```

## Step 3: Run Your First PPAC Decision

Invoke the brain with a simple prompt:

```bash
ai brain "What is the capital of France?"
```

You should see output from all five PPAC stages:

1. **Strategist** proposes candidate answers
2. **Predictor** tags them with confidence
3. **Accumulator** weighs evidence
4. **Actor** selects the highest-confidence option
5. **Critic** computes RPE based on the outcome

## Step 4: Verify Brain Region Activation

Check that every region fired:

```bash
ai brain regions
```

Each region should show a timestamp and a brief summary of its activity.

## Step 5: Explore Further

Now that you have a working installation:

- Read [../explanation/ARCHITECTURE.md](explanation/ARCHITECTURE.md) to understand how PPAC works
- Review [../reference/BASELINE.md](reference/BASELINE.md) for the full v0.1 feature set
- Follow [DEVELOPMENT.md](how-to/DEVELOPMENT.md) if you want to contribute

## Troubleshooting

**Ollama connection refused**

Ensure Ollama is running: `ollama serve`

**Model not found**

Verify the model name in `~/.brainxio/models.json` matches an installed Ollama model: `ollama list`

**Permission denied on `~/.brainxio/`**

Create the directory manually: `mkdir -p ~/.brainxio/rules ~/.brainxio/skills`

______________________________________________________________________

Congratulations! You have completed the getting-started tutorial.
