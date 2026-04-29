#!/bin/bash
set -e
cd "$(git rev-parse --show-toplevel)"
echo "=== Local CI Gate ==="
uv run ruff check . || { echo "ruff check failed"; exit 1; }
uv run ruff format --check . || { echo "ruff format check failed"; exit 1; }
uv run pytest -q || { echo "pytest failed"; exit 1; }
uv run mdformat --check docs/ *.md 2>/dev/null || { echo "mdformat check failed"; exit 1; }
echo "=== All checks passed ==="
