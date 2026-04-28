---
title: "Project Reference"
aliases: ["Reference"]
tags: [reference, docs]
created: 2026-04-28
updated: 2026-04-28
---

# Reference

## Entry Points

| Entry Point | Module | Description |
|-------------|--------|-------------|
| `ai` | `another_intelligence.cli:main` | Core CLI for brain operations |

## Core Modules

| Module | Description |
|--------|-------------|
| `another_intelligence.brain` | DigitalBrain orchestrator with PPAC loop |
| `another_intelligence.events` | Typed event bus |
| `another_intelligence.state` | Activity phase state machine |
| `another_intelligence.context` | Context window tracker |
| `another_intelligence.models.client` | Ollama client wrapper |
| `another_intelligence.models.resolver` | Tiered model resolver |
| `another_intelligence.permissions.engine` | Capability-based permissions engine |
| `another_intelligence.knowledge.compiler` | Daily log → structured articles |
| `another_intelligence.knowledge.query` | Knowledge base search |

## CLI Commands

| Command | Description |
|---------|-------------|
| `ai compile` | Parse daily logs and produce structured knowledge articles |
| `ai query` | Search the compiled knowledge base |

## Exported Classes

| Class | Module |
|-------|--------|
| `DigitalBrain` | `another_intelligence.brain` |
| `BrainEvent` | `another_intelligence.events` |
| `StateMachine` | `another_intelligence.state` |
| `ContextWindow` | `another_intelligence.context` |
| `PermissionEngine` | `another_intelligence.permissions.engine` |
| `KnowledgeCompiler` | `another_intelligence.knowledge.compiler` |
| `KnowledgeQuery` | `another_intelligence.knowledge.query` |
| `Article` | `another_intelligence.knowledge.compiler` |
