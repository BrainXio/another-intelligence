---
title: "Development Workflow & Tooling"
version: "0.1"
status: draft
updated: "2026-04-28"
---

# DEVELOPMENT.md — Development Workflow & Tooling

## 1. Philosophy

Another-Intelligence is developed with **extreme discipline** around tooling, testing, and autonomy. The goal is to enable a Claude-agent-sdk (or future self-hosted version) to implement large portions of the system with minimal human intervention while maintaining high code quality and security.

**Core Rules**
- Use `uv` for all Python package management (never `pip install --break-system-packages`).
- Use `npm` / `pnpm` for all JavaScript/TypeScript work.
- Everything is test-driven. No code is merged without passing tests.
- The autonomous agent loop (Claude-agent-sdk + MCP servers) is a first-class citizen of the development process.
- Documentation and architecture are updated **before** implementation begins.

---

## 2. Environment Setup

### 2.1 Prerequisites
- Python 3.12+
- Node.js 20+
- uv (latest)
- npm or pnpm
- Ollama running locally with at least one model pulled (`qwen3.5:14b` or equivalent recommended for development)
- Git

### 2.2 Initial Setup

```bash
# Clone the repo (once public)
git clone https://github.com/brainxio/another-intelligence.git
cd another-intelligence

# Python environment
uv venv
source .venv/bin/activate          # or equivalent on Windows
uv pip install -e ".[dev]"

# JavaScript (if working on web/UI/browser layers)
npm install
# or
pnpm install
```

### 2.3 Recommended IDE / Editor Settings
- VS Code + recommended extensions (Pylance, Ruff, ESLint, Markdownlint)
- Ruff for Python linting/formatting (configured in `pyproject.toml`)
- Pre-commit hooks (installed via `uv pip install pre-commit && pre-commit install`)

---

## 3. Daily Development Workflow

### 3.1 Starting Work on a Feature

1. Read the relevant documents:
   - `ARCHITECTURE.md`
   - `BASELINE.md` (if working toward v0.1)
   - The specific `.md` file for the area (e.g., `HOOKS.md`, `MCP.md`)
2. Create a feature branch: `git checkout -b feat/add-mcp-memory-server`
3. Write or update tests **first** (TDD).
4. Implement until all tests pass.
5. Update documentation if behavior changed.
6. Run full test suite + linting.
7. Open PR with clear description referencing the relevant `.md` files.

### 3.2 Running Tests

```bash
# Python tests
uv run pytest -q

# With coverage
uv run pytest --cov=src/another_intelligence --cov-report=term-missing

# JavaScript / browser tests (when applicable)
npm test
# or
pnpm test
```

### 3.3 Running the CLI during development

```bash
# After editable install
ai --help
ai status --extended
ai brain "Explain the PPAC loop in simple terms"
```

---

## 4. Autonomous Development Loop (Recommended)

Another-Intelligence is explicitly designed to be developed with heavy assistance from an LLM agent.

### 4.1 Recommended Setup for Autonomous Work

1. Install the following MCP servers globally or in your environment:
   - `@modelcontextprotocol/server-filesystem`
   - `@modelcontextprotocol/server-puppeteer` (or Playwright equivalent)
   - `@modelcontextprotocol/server-git`
   - Any additional servers you find useful (Serena, Memory, etc.)

2. Configure `~/.brainxio/mcp.json` (or project `.brainxio/mcp.json`) to point to these servers.

3. Use a Claude Code / Cline / similar agent with the following context loaded automatically:
   - `ARCHITECTURE.md`
   - `BASELINE.md`
   - `DEVELOPMENT.md`
   - `HOOKS.md`
   - `PERMISSIONS.md`
   - `MCP.md`

4. Instruct the agent with clear, bounded tasks such as:
   > "Implement the PreToolUse hook registration system according to HOOKS.md. Write tests first. All changes must pass `uv run pytest`."

### 4.2 Best Practices for Agent-Assisted Development

- Give the agent **small, well-scoped tasks**.
- Require it to update `PROGRESS.md` (or a task-specific note) after each major step.
- Always ask the agent to run the test suite and report results before considering work complete.
- Use `PreToolUse` hooks (once implemented) to add safety rails around file system and shell access.

---

## 5. Code Style & Quality Gates

### Python
- Follow PEP 8 + Ruff rules (configured in `pyproject.toml`).
- Type hints are **mandatory** on all public functions and classes.
- Use Pydantic for all configuration and data models.
- Maximum line length: 100 characters.

### JavaScript / TypeScript
- Follow the ESLint + Prettier config in the repo.
- Prefer TypeScript for any new code.

### Documentation
- Every public module, class, and function must have a docstring.
- Architecture or behavior changes **must** update the relevant `.md` file in `docs/`.

### Commit Messages
Use Conventional Commits:
```
feat(hooks): add typed PreToolUse event system
fix(permissions): prevent bypass of explicit deny rules
docs(architecture): clarify MCP client security model
test(baseline): add 5 new PPAC loop scenarios
```

---

## 6. Release Process (v0.1 and beyond)

1. All baseline criteria in `BASELINE.md` are green.
2. Full test suite passes with ≥ 80% coverage on core.
3. Documentation is complete and consistent.
4. `CHANGELOG.md` is updated.
5. Version bump in `pyproject.toml`.
6. Tag and push (after clean git re-initialization to public repo).

---

## 7. Common Commands Cheat Sheet

```bash
# Environment
uv sync
source .venv/bin/activate

# Testing
uv run pytest -q --tb=no
uv run ruff check .
uv run ruff format --check .

# Running
ai status
ai brain "Your prompt here" --json

# Autonomous agent helpers (examples)
claude --mcp-config ~/.brainxio/mcp.json
# or use your preferred agent with the docs/ folder in context
```

---

**End of DEVELOPMENT.md**

*This document should be read by every contributor and every autonomous agent working on the project.*
