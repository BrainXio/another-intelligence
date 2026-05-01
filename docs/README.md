---
title: Another-Intelligence Documentation
aliases: [Docs]
tags: [docs, index, diataxis]
created: '2026-05-01'
updated: '2026-05-01'
---

# Documentation

The Another-Intelligence documentation follows the **Diátaxis** framework, organized into four categories based on what the reader needs:

| Category                    | Purpose             | If you need to...                       |
| --------------------------- | ------------------- | --------------------------------------- |
| [Tutorials](tutorials/)     | Learn by doing      | Get started with a hands-on walkthrough |
| [How-to Guides](how-to/)    | Solve a problem     | Accomplish a specific task              |
| [Explanation](explanation/) | Understand concepts | Learn why things work the way they do   |
| [Reference](reference/)     | Look up facts       | Find precise technical information      |

## Tutorials

Step-by-step introductions for learners:

- [Getting Started](tutorials/getting-started.md) — Install, configure, and run your first PPAC decision

## How-to Guides

Task-oriented guides for practitioners:

- [DEVELOPMENT.md](how-to/DEVELOPMENT.md) — Development workflow and tooling
- [MIGRATION.md](how-to/MIGRATION.md) — Migrating from the prototype
- [PLUGIN-DEVELOPMENT.md](how-to/PLUGIN-DEVELOPMENT.md) — Writing plugins
- [PROMPTING.md](how-to/PROMPTING.md) — Prompt engineering and rules

## Explanation

Understanding-oriented documents that explain concepts and rationale:

- [ARCHITECTURE.md](explanation/ARCHITECTURE.md) — System architecture and design principles
- [MODEL-SCALING.md](explanation/MODEL-SCALING.md) — Tiered model scaling philosophy

## Reference

Fact-oriented documents that describe the system precisely:

- [BASELINE.md](reference/BASELINE.md) — v0.1 acceptance criteria
- [HOOKS.md](reference/HOOKS.md) — Hook system specification
- [MCP.md](reference/MCP.md) — Model Context Protocol integration
- [MCP-INTEGRATION-TESTING.md](reference/MCP-INTEGRATION-TESTING.md) — MCP integration testing
- [PERMISSIONS.md](reference/PERMISSIONS.md) — Capability-based permissions
- [planning.md](reference/planning.md) — Project planning and roadmap
- [README.md](reference/README.md) — API and module reference

______________________________________________________________________

All documents use YAML frontmatter with `title`, `tags`, `created`, and `updated` fields. Tags indicate the Diátaxis quadrant for easy filtering.
