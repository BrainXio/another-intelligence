---
title: Model Scaling and Tiered Intelligence
aliases: [Model Scaling, Tiered Intelligence]
tags: [architecture, scaling, models, ppac]
created: '2026-05-01'
updated: '2026-05-01'
---

# Model Scaling and Tiered Intelligence

Another-Intelligence (Cerebro) intelligently scales its cognitive capacity between cloud subscription tiers and specialized local models, matching intelligence level to task demands while staying sovereign and cost-aware.

## The Scaling Parallel

Biological brains do not run at maximum capacity for every thought. They allocate energy dynamically: intense focus for hard problems, efficient routine processing for everyday tasks, and minimal activity during rest. Cerebro mirrors this by treating computational resources and model power as adaptive rather than fixed.

Instead of locking into one model size or always using the most expensive option, Cerebro becomes a **parameterized, tier-aware cognitive system** that scales up for heavy work and down for light or idle tasks.

## Core Behavior

Cerebro continuously evaluates:

- Task complexity and expected value (via PPAC)
- Available hardware
- Internet connectivity and subscription tier
- Current load and energy/cost constraints

It then selects the most appropriate model variant from the `Another-Intelligence/*` namespace.

### Tiered Model Tags

| Tier              | Tag Example                        | Use Case                           | Characteristics                           |
| ----------------- | ---------------------------------- | ---------------------------------- | ----------------------------------------- |
| Cloud Max         | `cloud-max`                        | Heavy reasoning, complex decisions | Highest intelligence, higher latency/cost |
| Cloud Pro         | `cloud-pro`                        | Medium tasks                       | Balanced performance                      |
| Cloud Free        | `cloud-free`                       | Light coordination                 | Lower intelligence, minimal cost          |
| Local Specialized | `local-strategist`, `local-reflex` | Idle, chat, routine monitoring     | Fast, private, hardware-optimized         |

When a subscription is active and internet is available, Cerebro prefers cloud tiers for demanding work. When offline or for low-intensity tasks, it falls back to local specialized models.

## Nuances and Edge Cases Worth Considering

- **Graceful Degradation**: If the internet drops or the subscription lapses mid-task, Cerebro must seamlessly hand off to local models without losing state. The persistent memory, RPE logs, and shared bus are key to making this invisible to the user.
- **Cost vs Performance Awareness**: The Critic stage in the PPAC loop factors in an `efficiency_score` (normalized 0-1 combining actual latency, token cost, and energy draw) as part of expected value. Over time, RPE learning teaches the system when a higher tier is genuinely worth the premium.
- **Security and Sovereignty**: Sensitive tasks (personal notes, financial ideas, private data) default to local models. The permissions engine (see [../reference/PERMISSIONS.md](../reference/PERMISSIONS.md)) needs clear rules for when cloud scaling is allowed.
- **Model Discovery and Registration**: `ai_model_register` and `ai_model_evaluate` MCP tools expose capability metadata (size, tier, estimated latency, cost) so the orchestrator can make informed routing decisions. New models (local or cloud) need automatic discovery and self-evaluation. Discovery is owned by the Another-Intelligence MCP server, not by ADHD or OCD.
- **Transition Friction**: Switching models mid-session or mid-PPAC cycle requires careful state management. Short tasks may not justify the overhead of scaling up.
- **Subscription Edge Cases**: What happens on free-tier limits, rate-limiting, or temporary outages? Clear fallback policies and user notifications (via HITL) prevent silent degradation.
- **Hardware Variability**: Different GPUs or systems will have different local capabilities. The auto-selector must probe hardware realistically and avoid assuming uniform performance.
- **Learning from Scaling Decisions**: Every tier choice becomes training data. Positive/negative RPE on efficiency helps the system refine its scaling policy over time.
- **Namespace Placeholders**: The `Another-Intelligence/*` tags above are namespace placeholders. Actual model availability depends on Ollama registry configuration and local model files.

These considerations ensure scaling remains robust rather than brittle.

## Architecture

### Dynamic Selection Logic (PPAC Integration)

- **Proposer**: Generates candidate plans and estimates required intelligence level.
- **Predictor**: Tags plans with expected cost, latency, and privacy needs.
- **Accumulator**: Weighs evidence from current context (hardware, connection, subscription).
- **Actor**: Selects and routes to the appropriate model variant.
- **Critic**: Records RPE including efficiency (was the chosen tier worth it?) for future learning.

Model switching is handled gracefully via Ollama. No session loss occurs because state persists through the shared bus and KB.

### Configuration

Global configuration lives in `~/.brainxio/` with overrides possible per project.

Example environment variables:

```bash
# Enable subscription-aware scaling
CEREBRO_ENABLE_SCALING=1

# Set subscription tier (detected automatically when possible)
CEREBRO_SUBSCRIPTION_TIER=max
```

### Fallback and Graceful Degradation

- No internet or subscription: automatically uses local models.
- Cloud model unavailable: falls back to next best available tier.
- Hardware constraints detected: prefers lighter local variants.

## Quick Start

After installing the specialized models:

```bash
# Pull tiered models (example)
ollama pull another-intelligence/cloud-max
ollama pull another-intelligence/local-reflex

# Run with scaling enabled
ai brain "Analyze this complex market data" --scaling
```

Cerebro will handle tier selection transparently. The `Another-Intelligence/*` model names are placeholders; actual names depend on your Ollama registry configuration.

## Philosophy

- **Adaptive over static**: Intelligence should match the moment, not be fixed.
- **Sovereign by default**: Local models first, cloud only when beneficial.
- **Cost and energy aware**: Treat resources as part of the decision process.
- **Universal compatibility**: Works with any MCP-compliant framework; scaling logic lives in Cerebro.

## Roadmap

- Initial implementation: Basic tier detection and fallback.
- Self-evaluation: Models rate their own suitability during tasks.
- Advanced routing: Per-driver specialization (for example, heavier model for ASD synthesis).
- Earnings-driven growth: Use generated revenue to expand hardware or subscription.

This scaling system turns Cerebro into a living, breathing cognitive exoskeleton that grows with you: efficient when possible, powerful when needed, and always under your control.
