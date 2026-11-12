#!/usr/bin/env bash
# Run a CI check locally or in RWX: ci/run.sh <test|pyright|pyrefly|all> [args]
# Needs Docker and the `dagger` CLI (0.21.10, matching dagger-io in pyproject.toml).
set -euo pipefail
export PATH="${HOME}/.local/bin:${PATH}"
cd "$(dirname "$0")/.."
exec dagger run uv run python ci/main.py "$@"
