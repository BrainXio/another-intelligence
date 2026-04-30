# Contributing to Another-Intelligence

## Branch Naming

Use conventional prefix and a short kebab-case description:

| Prefix      | When to use                               |
| ----------- | ----------------------------------------- |
| `feat/`     | New feature or enhancement                |
| `fix/`      | Bug fix                                   |
| `docs/`     | Documentation changes only                |
| `chore/`    | Maintenance, tooling, CI, dependencies    |
| `refactor/` | Code restructuring without feature change |
| `test/`     | Test additions or improvements            |

Examples: `feat/rpe-telemetry`, `fix/permissions-path-resolution`, `docs/architecture-update`.

## Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>
```

Types: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `style`, `perf`.

Scopes for this repo: `brain`, `rpe`, `mcp`, `strategist`, `executor`, `reflex`, `memory`, `cli`, `docs`.

Keep the description concise and imperative (add, fix, remove — not adds, fixes, removed).

## PR Workflow

1. Create a feature branch from `main`

2. Implement with tests (TDD required)

3. Run the local CI gate before pushing:

   ```bash
   uv run ruff check .
   uv run ruff format --check .
   uv run pytest -q
   uv run mdformat --check README.md docs/
   ```

4. Push and open a PR against `main`

5. Post the PR URL to the ADHD bus for review

6. Do not self-merge — wait for a supporter review

## Code Style

- Type hints on all public functions and classes
- Line length: 100 characters
- Use Pydantic for configuration and data models
- Tests use `pytest` (not `unittest`)
- Imports sorted via `ruff` (enforced in CI)
- No attribution of any kind in commits, PRs, comments, or docs

## Architecture Principles

- All external tooling routes through the MCP client — no direct imports of non-standard-library packages
- The PPAC loop is strictly serial — no shortcuts, no parallel execution of decision stages
- Configuration lives in `~/.brainxio/` (global) and `.brainxio/` (project) — not in source code
- Every component should have a biological analogue documented in its module docstring

## Bus Communication

Post to the ADHD bus for coordination only — task claims, dependency declarations, blocker reports, PR announcements, or review requests. Before asking a question, check `docs/` first.
