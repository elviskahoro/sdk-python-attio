#!/usr/bin/env bash
# Regenerate the SDK on a host with no Docker/Dagger, using the host Speakeasy
# CLI. Prefer `uv run python ci/pipeline.py generate` where Dagger works; this
# is the fallback (see AGENTS.md). Never commits or pushes.
#
# Usage: ci/regenerate_host.sh [--fetch]   (--fetch adopts the latest upstream spec)
# Requires: SPEAKEASY_API_KEY, uv. Installs the pinned Speakeasy CLI if missing.
# The pin and checksum must match .rwx/regenerate.yml and ci/pipeline.py.

set -euo pipefail

cd "$(dirname "$0")/.."

SPEAKEASY_VERSION=1.804.0
INSTALLER_URL=https://raw.githubusercontent.com/speakeasy-api/speakeasy/89688fa0cfc3c959f4ac370329325d1b274db551/install.sh
INSTALLER_SHA256=9e2c4f1054e214d05352597cfd9ed1ab117a089e9442f532dd4a0d168665d757

generate_args=(--no-fetch)
case "${1:-}" in
"") ;;
--fetch) generate_args=() ;;
*)
	echo "usage: $0 [--fetch]" >&2
	exit 2
	;;
esac

if [[ -z ${SPEAKEASY_API_KEY:-} ]]; then
	echo "SPEAKEASY_API_KEY is not set" >&2
	exit 1
fi

if ! command -v speakeasy >/dev/null 2>&1; then
	installer="$(mktemp)"
	trap 'rm -f "$installer"' EXIT
	curl -fsSL -o "${installer}" "${INSTALLER_URL}"
	echo "${INSTALLER_SHA256}  ${installer}" | sha256sum -c -
	VERSION="${SPEAKEASY_VERSION}" sh "${installer}"
fi

uv sync
SPEAKEASY_USE_HOST_CLI=1 uv run python ci/pipeline.py generate "${generate_args[@]}"
uv lock
uv run python ci/spec_diff.py check-overlay
uv run mypy generated/src
uv run pytest -q

git status --short
