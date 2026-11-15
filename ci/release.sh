#!/usr/bin/env bash
# End-to-end release: (optionally) bump the version through a PR, tag, publish
# attio + gtm-attio to PyPI via the RWX `publish` dispatch, and verify both
# packages are live.
#
# Real entrypoint lives in ci/ so Speakeasy generation can never overwrite it;
# scripts/release.sh is a thin wrapper that delegates here.
#
# Usage:
#   scripts/release.sh                 release the version already on main
#   scripts/release.sh --bump          patch-bump via a no-op regeneration, then release
#   scripts/release.sh 0.29.0          bump to 0.29.0 via regeneration, then release
#   scripts/release.sh --dry-run ...   print the plan; change nothing
#
# Bumps always go through Speakeasy (ci/regenerate_host.sh), so gen.yaml,
# gen.lock, _version.py, pyproject.toml and uv.lock stay in lockstep. The bump
# lands as a PR merged with `gh pr merge --squash --auto`; main is never pushed
# to directly. Steps are idempotent: re-running after a failure skips a tag that
# already points at the right commit and packages already on PyPI.
#
# Needs: git, gh (authenticated), uv, curl, rwx (RWX_ACCESS_TOKEN, or
# RWC_ACCESS_TOKEN_ELVISKAHORO which is mapped in); a bump also needs
# SPEAKEASY_API_KEY.

# Command substitutions inside conditions are intentional (failures there are
# handled explicitly), so the "masked return value" style checks do not apply.
# shellcheck disable=SC2312,SC2310
set -euo pipefail

PACKAGES=(attio gtm-attio)
MERGE_TIMEOUT_SECONDS="${RELEASE_MERGE_TIMEOUT_SECONDS:-3600}"
PYPI_TIMEOUT_SECONDS="${RELEASE_PYPI_TIMEOUT_SECONDS:-600}"

mode="current"
target=""
dry_run=0

usage() {
	sed -n '9,14p' "$0" | sed 's/^# \{0,1\}//' >&2
	exit 2
}

for arg in "$@"; do
	case "${arg}" in
	--bump) mode="bump" ;;
	--dry-run) dry_run=1 ;;
	-h | --help) usage ;;
	-*) usage ;;
	*)
		[[ -z ${target} ]] || usage
		target="${arg}"
		mode="set"
		;;
	esac
done

if [[ ${mode} == set ]] && ! [[ ${target} =~ ^[0-9]+\.[0-9]+\.[0-9]+([a-zA-Z0-9.+-]*)?$ ]]; then
	echo "Error: '${target}' does not look like a version (e.g. 0.29.0 or 1.0.0rc1)" >&2
	exit 2
fi

log() { printf '\n==> %s\n' "$*" >&2; }
die() {
	printf 'Error: %s\n' "$*" >&2
	exit 1
}
run() {
	if ((dry_run)); then
		printf '[dry-run] %s\n' "$*" >&2
	else
		"$@"
	fi
}

committed_version() {
	sed -n 's/^__version__: str = "\(.*\)"$/\1/p' generated/src/attio/_version.py
}

on_pypi() { # on_pypi PACKAGE VERSION
	curl -fsS -o /dev/null "https://pypi.org/pypi/$1/$2/json" 2>/dev/null
}

# --- Preflight ---------------------------------------------------------------

cd "$(git rev-parse --show-toplevel)"

for tool in git gh uv curl rwx; do
	command -v "${tool}" >/dev/null 2>&1 || die "${tool} is not on PATH"
done
if [[ -z ${RWX_ACCESS_TOKEN:-} ]]; then
	[[ -n ${RWC_ACCESS_TOKEN_ELVISKAHORO:-} ]] ||
		die "set RWX_ACCESS_TOKEN (or RWC_ACCESS_TOKEN_ELVISKAHORO) for the elviskahoro RWX org"
	export RWX_ACCESS_TOKEN="${RWC_ACCESS_TOKEN_ELVISKAHORO}"
fi
gh auth status >/dev/null 2>&1 || die "gh is not authenticated (gh auth login)"
if [[ ${mode} != current && -z ${SPEAKEASY_API_KEY:-} ]]; then
	die "SPEAKEASY_API_KEY is required to bump the version (regeneration)"
fi

[[ -z "$(git status --porcelain)" ]] || {
	git status --short >&2
	die "working tree is dirty; commit or stash first"
}
[[ "$(git rev-parse --abbrev-ref HEAD)" == main ]] || die "check out main first"
git fetch -q origin main --tags
git merge -q --ff-only origin/main

# --- Bump (optional) ---------------------------------------------------------

if [[ ${mode} != current ]]; then
	before="$(committed_version)"
	branch="release/bump-$(date -u +%Y%m%d%H%M%S)"
	log "Bumping from ${before} on ${branch}"
	run git checkout -q -b "${branch}"
	if [[ ${mode} == set ]]; then
		# Speakeasy releases the version set in gen.yaml when it is ahead of
		# the last generated one; the regeneration below writes it everywhere.
		run sed -i.bak "s/^  version: .*/  version: ${target}/" .speakeasy/gen.yaml
		run rm -f .speakeasy/gen.yaml.bak
	fi
	run ci/regenerate_host.sh
	if ((dry_run)); then
		version="${target:-<next patch>}"
	else
		version="$(committed_version)"
		[[ ${version} != "${before}" ]] || die "regeneration did not change the version (still ${before})"
		[[ ${mode} != set || ${version} == "${target}" ]] ||
			die "regeneration produced ${version}, expected ${target}"
	fi
	run git add -A generated .speakeasy pyproject.toml uv.lock README.md
	run git commit -q -m "Bump version to ${version}"
	run git push -q -u origin "${branch}"
	if ((dry_run)); then
		printf '[dry-run] gh pr create + gh pr merge --squash --auto, then wait for the merge\n' >&2
	else
		pr_url="$(gh pr create --base main --head "${branch}" \
			--title "Bump version to ${version}" \
			--body "Release bump ${before} → ${version} via \`ci/release.sh\` (no-op regeneration, unchanged spec).")"
		gh pr merge "${pr_url}" --squash --auto
		log "Waiting for ${pr_url} to merge (timeout ${MERGE_TIMEOUT_SECONDS}s)"
		deadline=$((SECONDS + MERGE_TIMEOUT_SECONDS))
		until [[ "$(gh pr view "${pr_url}" --json state --jq .state)" == MERGED ]]; do
			state="$(gh pr view "${pr_url}" --json state --jq .state)"
			[[ ${state} != CLOSED ]] || die "${pr_url} was closed without merging"
			((SECONDS < deadline)) || die "${pr_url} did not merge in time; re-run scripts/release.sh once it lands"
			sleep 30
		done
		git checkout -q main
		git fetch -q origin main
		git merge -q --ff-only origin/main
	fi
	if ((dry_run)); then
		run git checkout -q main
	fi
else
	version="$(committed_version)"
fi

tag="v${version}"
log "Releasing ${tag} ($(git rev-parse --short HEAD))"

# --- Already released? -------------------------------------------------------

pending=()
for pkg in "${PACKAGES[@]}"; do
	if on_pypi "${pkg}" "${version}"; then
		echo "${pkg} ${version} is already on PyPI" >&2
	else
		pending+=("${pkg}")
	fi
done
if ((${#pending[@]} == 0)); then
	echo "Nothing to do: every package already has ${version} on PyPI." >&2
	exit 0
fi

# --- Tag ---------------------------------------------------------------------

head_sha="$(git rev-parse HEAD)"
remote_tag_sha="$(git ls-remote origin "refs/tags/${tag}^{}" | cut -f1)"
[[ -n ${remote_tag_sha} ]] || remote_tag_sha="$(git ls-remote origin "refs/tags/${tag}" | cut -f1)"
if [[ -n ${remote_tag_sha} ]]; then
	# A retry after a failed publish: keep the existing tag if it is ours.
	tagged_version="$(git show "${remote_tag_sha}:generated/src/attio/_version.py" 2>/dev/null |
		sed -n 's/^__version__: str = "\(.*\)"$/\1/p')"
	[[ ${tagged_version} == "${version}" ]] ||
		die "${tag} already exists on origin at ${remote_tag_sha} with version '${tagged_version}'"
	echo "${tag} already on origin (${remote_tag_sha:0:7}); reusing it" >&2
else
	run git tag -a "${tag}" "${head_sha}" -m "${tag}"
	run git push -q origin "${tag}"
fi

# --- Publish -----------------------------------------------------------------

log "Dispatching the RWX publish run for ${tag}"
run rwx dispatch publish --ref main --param "tag=${tag}" --title "Publish ${tag}" --wait

# --- Verify ------------------------------------------------------------------

if ((dry_run)); then
	printf '[dry-run] wait for %s %s on PyPI, then smoke-test with uvx\n' "${PACKAGES[*]}" "${version}" >&2
	exit 0
fi

log "Waiting for PyPI to serve ${version}"
deadline=$((SECONDS + PYPI_TIMEOUT_SECONDS))
for pkg in "${PACKAGES[@]}"; do
	until on_pypi "${pkg}" "${version}"; do
		((SECONDS < deadline)) || die "${pkg} ${version} is not on PyPI after ${PYPI_TIMEOUT_SECONDS}s"
		sleep 10
	done
	echo "${pkg} ${version} is on PyPI" >&2
done

for pkg in "${PACKAGES[@]}"; do
	out="$(uvx --refresh --from "${pkg}==${version}" "${pkg}" --version 2>/dev/null)" ||
		die "uvx could not run ${pkg}==${version}"
	[[ ${out} == "${pkg} ${version}" ]] || die "${pkg} reported '${out}', expected '${pkg} ${version}'"
	echo "uvx ${pkg}@${version} --version -> ${out}" >&2
done

log "Released ${version}: https://pypi.org/project/attio/${version}/ and https://pypi.org/project/gtm-attio/${version}/"
