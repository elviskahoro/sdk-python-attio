#!/usr/bin/env bash
set -euo pipefail

# Conductor preflight script to initialize uv environment before trunk checks.
# Run before trunk check to ensure .venv exists for pyright and pyrefly.
# See issue #50: trunk check requires uv sync to be run before checking.

if ! command -v uv &>/dev/null; then
	echo "uv not installed; skipping preflight" >&2
	exit 0
fi

if [[ ! -d .venv ]]; then
	echo "Initializing Python environment with uv sync..."
	uv sync
else
	echo "Python environment already initialized (.venv exists)"
fi
