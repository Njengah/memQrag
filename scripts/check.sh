#!/usr/bin/env bash
# Run the standard memQrag verification checks locally.
#
# Mirrors .github/workflows/ci.yml. See docs/DECISIONS.md ("CI And Local
# Check Scripts") for what each check covers and why.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

echo "==> Backend: ruff lint"
python -m ruff check .

echo "==> Backend: ruff format check"
python -m ruff format --check .

echo "==> Backend: pytest"
python -m pytest

echo "==> Frontend: lint (oxlint)"
(cd ui && npm run lint)

echo "==> Frontend: build (tsc + vite build)"
(cd ui && npm run build)

echo "All checks passed."
