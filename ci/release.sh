#!/usr/bin/env bash
# Cut a new release: bump version in pyproject.toml + src/attio/_version.py
# via the Dagger pipeline, commit, tag, and push. The Publish to PyPI workflow
# fires on the tag push.
#
# Real entrypoint lives in ci/ so Speakeasy generation can never overwrite it;
# scripts/release.sh is a thin wrapper that delegates here.
#
# Usage: ci/release.sh 0.22.9   (same as scripts/release.sh 0.22.9)

set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <version>  e.g. $0 0.22.9" >&2
  exit 2
fi

version="$1"

if ! [[ ${version} =~ ^[0-9]+\.[0-9]+\.[0-9]+([a-zA-Z0-9.+-]*)?$ ]]; then
  echo "Error: '${version}' does not look like a SemVer (e.g. 0.22.9 or 1.0.0rc1)" >&2
  exit 2
fi

repo_root="$(git rev-parse --show-toplevel)"
cd "${repo_root}"

status_output="$(git status --porcelain)"
if [[ -n ${status_output} ]]; then
  echo "Error: working tree is dirty. Commit or stash changes first." >&2
  git status --short >&2
  exit 1
fi

branch="$(git rev-parse --abbrev-ref HEAD)"
if [[ ${branch} != "main" ]]; then
  echo "Error: not on main (current: ${branch}). Release from main." >&2
  exit 1
fi

if git rev-parse -q --verify "refs/tags/v${version}" >/dev/null; then
  echo "Error: tag v${version} already exists locally." >&2
  exit 1
fi

if git ls-remote --exit-code --tags origin "refs/tags/v${version}" >/dev/null 2>&1; then
  echo "Error: tag v${version} already exists on origin." >&2
  exit 1
fi

git pull --ff-only origin main

# Bump versions inside a Dagger container and export the patched files back.
if ! uv run python ci/pipeline.py release-bump "${version}"; then
  echo "Error: version bump failed" >&2
  exit 1
fi

# Sanity check: confirm both files agree with the requested version.
uv run python ci/pipeline.py verify-version "${version}"

git add pyproject.toml src/attio/_version.py
git commit -m "chore: bump version to ${version}"
git tag "v${version}"
git push origin main "v${version}"

echo
echo "Pushed v${version}. Watch the publish run:"
echo "  gh run watch \$(gh run list --workflow='Publish to PyPI' --limit 1 --json databaseId -q '.[0].databaseId')"
