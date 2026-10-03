#!/usr/bin/env bash
# Real publish entrypoint. Lives in ci/ so Speakeasy generation can never
# overwrite it; scripts/publish.sh is a thin wrapper that delegates here.

set -euo pipefail

cd "$(dirname "$0")/.."

# The SDK has custom staging logic and produces both attio and gtm-attio.
# Build those artifacts once, then let the shared module receive the token as
# a Dagger Secret rather than exposing it to uv or the shell command line.
uv run --env-file .env.local python ci/pipeline.py publish
