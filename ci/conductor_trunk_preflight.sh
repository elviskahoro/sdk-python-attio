#!/usr/bin/env bash
set -euo pipefail

# Conductor preflight script to initialize uv environment before trunk checks.
# Run before trunk check to ensure .venv is in sync for pyright and pyrefly.
# See issue #50: trunk check requires uv sync to be run before checking.

if ! command -v uv &>/dev/null; then
	echo "uv is required but not found on PATH; cannot initialize .venv" >&2
	exit 1
fi

# Always sync: .venv may be stale after uv.lock/pyproject.toml changes or a
# partially failed earlier sync. uv sync is a fast no-op when up to date.
echo "Syncing Python environment with uv sync..."
uv sync
