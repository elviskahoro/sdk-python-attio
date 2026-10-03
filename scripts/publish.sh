#!/usr/bin/env bash
# Thin wrapper — do not add logic here.
#
# `speakeasy run` regenerates scripts/ with its own templates (see
# .genignore), so this file deliberately only delegates to the real
# implementation in ci/, which the generator never touches.
# ci/post_generate_patch.py restores this wrapper after every regeneration
# in case it is ever overwritten anyway.
set -euo pipefail
exec bash "$(dirname "$0")/../ci/publish.sh" "$@"
