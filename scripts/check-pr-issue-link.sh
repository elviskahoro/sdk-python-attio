#!/usr/bin/env bash
# Fail unless the PR body ($PR_BODY) ties the PR to an issue, so merge closes the
# issue and the claim (status::in_progress) is released. Accepts, case-insensitive:
#   Closes|Fixes|Resolves #N      (full resolve; GitHub auto-closes on merge)
#   Refs|Part of #N               (partial work; issue stays open)
#   No issue: <reason>            (deliberate, e.g. chore or release)
# Bot PRs (PR_AUTHOR ending in [bot], e.g. dependabot) are skipped.
# Usage: PR_BODY=... [PR_AUTHOR=...] check-pr-issue-link.sh
set -uo pipefail
if [[ ${PR_AUTHOR:-} == *"[bot]" ]]; then
	echo "OK: skipped bot PR (${PR_AUTHOR})."
	exit 0
fi
pat='((close[sd]?|fix(es|ed)?|resolve[sd]?|refs?|part of)[[:space:]]+([[:alnum:]_.-]+/[[:alnum:]_.-]+)?#[0-9]+)|(^|[[:space:]])no issue:[[:space:]]*[^[:space:]]'
if grep -qiE "${pat}" <<<"${PR_BODY:-}"; then
	echo "OK: PR body links an issue (or says why not)."
	exit 0
fi
echo "FAIL: PR body must contain 'Closes #N' (or Fixes/Resolves), 'Refs #N' for partial work, or 'No issue: <reason>'."
echo "Why: the closing keyword closes the issue on merge and signals the claim can be released."
exit 1
