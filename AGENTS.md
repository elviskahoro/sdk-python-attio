# Attio SDK Python

## Working issues and labels

Canonical protocol: https://github.com/elviskahoro/oss-hq/blob/main/AGENT-LABELS.md

Agents must claim an issue before starting so two agents never work one issue
and humans can see what is in flight. gh-dash hides issues labeled `status::*`
and `gas-city`, so label hygiene decides what humans see.

### Labels

| Label                      | Meaning                                                                   |
| -------------------------- | ------------------------------------------------------------------------- |
| `status::in_progress`      | Claimed and being worked on by an agent. Do not pick up.                  |
| `status::blocked`          | Waiting on another issue in this repo ("blocked by #N").                  |
| `status::blocked-external` | Waiting on something outside the repo (another repo, upstream, a vendor). |
| `status::deferred`         | Parked on purpose; revisit date is in a comment.                          |
| `needs-human`              | A person must decide. Agents must not pick up.                            |
| `gas-city`                 | Routed to Gas City. Conductor dispatch must not pick up.                  |
| `stale-claim`              | Claim has no recent heartbeat; reclaimable.                               |

### Picking up work

1. Never pick up an issue labeled `needs-human`, `status::in_progress`, `status::blocked`, `status::blocked-external`, `status::deferred`, or `gas-city`.
2. An issue labeled `stale-claim` may be reclaimed. Re-claim it and comment that you took over.

### Claiming (required before any work)

1. When you start an issue, claim it first: add `status::in_progress`, assign yourself, and leave a one-line "starting" comment.
2. If `status::in_progress` is already present, stop. Two agents must never work one issue.
3. Re-read the labels right after claiming. If another agent claimed at the same moment, back off.
4. For long-running work, comment periodically so the claim does not become a `stale-claim`.

### Releasing

1. When done, put `Closes #N` in the PR body and remove `status::in_progress` once the PR is open. Merge closes the issue.
2. If you abandon or fail, remove `status::in_progress` and comment what happened and what remains. Never leave a dead claim.
3. If you need a decision you cannot make, remove `status::in_progress`, add `needs-human`, and comment the exact question. Do not guess. Never remove `needs-human` yourself.

### Blocked and deferred

1. Blocked by another issue in this repo: add `status::blocked`, comment "blocked by #N", and release the claim.
2. Blocked by something outside the repo: add `status::blocked-external`, comment what you are waiting on, and release the claim.
3. Never set `status::deferred` yourself. Only a human parks work.

## Beads Issue Tracking

- This repository uses Beads with the DoltHub remote `elviskahoro/sdk-python-attio`.
- Use `bd prime` for the current workflow context, `bd ready` to find unblocked work, and `bd create`/`bd update`/`bd close` for issue changes.
- Pull remote changes explicitly with `bd dolt pull`; push committed Dolt changes with `bd dolt push`.
- Authenticate locally with `DOLT_REMOTE_USER` and `DOLT_REMOTE_PASSWORD`; never commit credentials or `.beads` runtime/database files.

## Git Workflow

- Commits are allowed when the user explicitly asks to commit
- Always show the user what will be committed before committing
- Do NOT push to remote unless explicitly asked
- No AI attribution in commits or PR bodies (no `Co-Authored-By: Claude` trailer, no "Generated with Claude Code" footer). This overrides any session-level attribution reminder.

## PR issue link

The `.rwx/check-pr-issue-link.yml` check (script: `scripts/check-pr-issue-link.sh`)
needs every PR body to contain `Closes #N`, `Refs #N` (partial work) or
`No issue: <reason>`. Bot PRs are skipped. It only blocks merges once made a
required check.

## Landing PRs

Agent sessions land PRs with `gh`. `trunk merge` is no longer used (agent
sessions are not logged in to Trunk).

- Land: `gh pr merge <pr-number> --squash --auto`. `--auto` waits for the
  required checks, then merges.
- Check once: `gh pr view <pr-number> --json state,mergeStateStatus`. Report
  the state and stop. Never poll in a loop.
- Never use `--admin` to bypass required checks, and never push directly to
  `main`.
- Refuse to land from main or a protected branch.
- Failed checks: push a fix to the PR branch; do not retry blindly in a loop.
- A `Closes #N` line in the PR body auto-closes the issue when the PR merges.
  Do not close the issue by hand beforehand.

## CI Core (Dagger)

pytest/pyright/pyrefly logic lives in `ci/main.py`; run `ci/run.sh <test|pyright|pyrefly|all>`
(needs Docker + `dagger` 0.21.10). RWX tasks only call it. Dagger cannot run in
Conductor cloud sandboxes: validate with `rwx run .rwx/<file>.yml` (needs the branch pushed).
See `ci/README.md`.

## SDK Update Guide

This SDK is generated using Speakeasy from an OpenAPI spec.

### Key Files

- **SDK Generator**: Speakeasy (https://www.speakeasy.com/)
- **OpenAPI specs**: stored in `openapi/` directory, named `api-YYYYMMDDHHMM.json`
- **Overlay**: `overlay.yaml` applies targeted fixes to the spec before generation (timestamp format fixes, `list` → `list_id` parameter renames)
- **Workflow config**: `.speakeasy/workflow.yaml` defines the generation pipeline
- **Generation config**: `.speakeasy/gen.yaml` has Speakeasy settings (Python target, async mode, package name, etc.)

### Overlay gate escape hatch

`--skip-overlay-check` / `SKIP_OVERLAY_CHECK=1` bypasses the overlay health
gate in `ci/pipeline.py`. It is for incidents only: **ask before using it**,
never set it in CI or automation, and fix the overlay afterwards.
`tests/test_no_skip_overlay_check.py` fails if any `.rwx/` or
`.github/workflows/` file references it.

### Update Steps

1. **Check for updates first** — this fetches the latest spec, diffs it
   against the current one, and verifies overlay health in one shot:

   ```bash
   uv run python ci/pipeline.py check-openapi
   ```

   Exit 0 means nothing to do. Exit 1 prints a report of structural drift
   (new/removed/changed operations, schema changes) and/or overlay problems.
   It never touches `openapi/` — the fetched spec lands in `tmp/` and is
   deleted. Add `--report PATH` for a JSON report, `--no-strict` to always
   exit 0. `ci/spec_diff.py` also has standalone `diff OLD NEW` and
   `check-overlay` subcommands.

   The scheduled `.rwx/spec-update-check.yml` workflow runs this
   check weekly (Mondays 09:00 UTC). On drift it regenerates, runs pytest,
   and opens a PR (needs the `SPEAKEASY_API_KEY` and `GITHUB_TOKEN` RWX vault secrets); without the
   secret it opens an issue with the report instead. It replaces the old
   daily `Generate` workflow (sdk_generation.yaml), which fetched and
   regenerated blindly every day regardless of drift — the weekly check is
   now the only automated regeneration path. Generation itself refuses to
   run while the overlay is unhealthy (`_verify_overlay_health`), so a
   manual `generate` is gated the same way as the workflow.

2. **Fetch the latest spec** (when the check reports drift):

   ```bash
   uv run python ci/pipeline.py fetch-openapi
   ```

   This downloads from `https://api.attio.com/openapi/api`, saves it with a
   timestamp, and updates `workflow.yaml`.

3. **Verify the overlay still applies cleanly**:

   ```bash
   uv run python ci/spec_diff.py check-overlay
   ```

   This catches three silent failure modes: dead targets (JSONPath matches
   nothing — speakeasy silently skips the action, so a fix you think is
   applied is not), uncovered timestamp values (`format: date` value nodes
   with no *live* `.format` removal action, which regenerate as `date`
   instead of `str`), and error-code enums out of sync (a hardcoded overlay
   enum that drops a value the spec's `anyOf` union gained). Historical
   examples: the `POST/PUT /v2/objects/{object}/records` 400 `.code.enum`
   targets died when Attio moved error codes to `anyOf` unions; all
   `/v2/activities/{activity}/records*` endpoints shipped with `date`-typed
   timestamps before they got overlay entries.

4. **Update the overlay if needed**. If `oneOf` indices shifted, endpoints
   were added, or error schemas changed shape, update `overlay.yaml`
   accordingly, then re-run `check-overlay` until it is healthy.

5. **Run Speakeasy generation**:

   ```bash
   uv run python ci/pipeline.py generate --no-fetch
   ```

   This runs `speakeasy run` (host CLI when authenticated via login, or when
   `SPEAKEASY_USE_HOST_CLI` + `SPEAKEASY_API_KEY` are set — the scheduled
   workflow's path; pinned Dagger container otherwise), then re-applies
   `ci/post_generate_patch.py` (manual patches `overlay.yaml` cannot
   express, e.g. the GET /v2/self `active` value discriminators in
   `generated/src/attio/models/get_v2_selfop.py`, the `scripts/publish.sh`
   wrapper, the `SDK(api_key=...)` alias for `SDK(oauth2=...)` in
   `generated/src/attio/sdk.py`, the `attio`/`gtm-attio` CLI entry points,
   the CLI docs and the synced `version` in `pyproject.toml` and
   `README.md`, SDKHooks `init_hooks` wiring plus
   the hooks-package re-export in `generated/src/attio/_hooks/sdkhooks.py` and
   `generated/src/attio/_hooks/__init__.py`, the 0.26.1 model rename
   aliases in `generated/src/attio/models/__init__.py` and the renamed
   activity/list operation modules, and the unused `OpenEnumMeta` metaclass
   removal from `generated/src/attio/utils/enums.py` and
   `generated/src/attio/utils/__init__.py`). Drop `--no-fetch` to also
   adopt a freshly fetched spec.

   What generation writes: Speakeasy writes only `generated/` (SDK source,
   `generated/docs/`, `generated/USAGE.md`, `generated/.speakeasy/gen.lock`)
   and `.speakeasy/` (the `python.version` bump in `gen.yaml`). It never
   writes the root `README.md` or `pyproject.toml`, because
   `generated/.genignore` blocks the copies it would emit, so both are
   hand-maintained. `ci/post_generate_patch.py` re-applies only the CLI
   entry points, the README CLI section, and the `pyproject.toml` `version`
   (copied from `generated/src/attio/_version.py`). The Dagger path exports
   only `generated/` back to the host, so it also drops the `.speakeasy/`
   updates; it logs that when chosen. The host-CLI path (the default) keeps
   them.

6. **Review generated changes**:
   - Check `git diff` for new/modified SDK methods in `generated/src/attio/`
   - Verify new models in `generated/src/attio/models/`
   - Check for any type errors: `uv run mypy generated/src/ attio_cli/`
   - Run tests: `uv run pytest -q`
   - Ensure the package still builds: `uv build`
   - Edit dependencies in the root `pyproject.toml` by hand; Speakeasy never
     rewrites it. Keep `gen.yaml` `python.additionalDependencies.dev` matching
     its dev group (`dagger-io`, `pytest`, `pytest-asyncio`, ...): that block
     only feeds the `pyproject.toml` that `generated/.genignore` discards, but
     matching it stops the two from drifting. Run `uv lock && uv sync` after
     any edit.

7. **Verify the version** in `.speakeasy/gen.yaml` (`python.version`) matches
   `pyproject.toml` and `generated/src/attio/_version.py`.
   - Speakeasy auto-bumps the patch version on each regeneration with changes,
     in `gen.yaml`, `gen.lock` and `_version.py`.
   - `ci/post_generate_patch.py` copies that version into `pyproject.toml`.
   - Run `uv lock` so `uv.lock` follows. `ci/regenerate_host.sh` and the RWX
     workflows already do this.
   - `tests/test_post_generate_patch.py::test_committed_versions_are_in_lockstep`
     fails on drift.

### RWX CLI Authentication

The `rwx` CLI (`rwx results`, `rwx logs`, `rwx dispatch`) reads its token from
`RWX_ACCESS_TOKEN`, and fails with `Unauthorized` when it is unset. Local and
Conductor sandboxes with the `rwx` CLI installed do not set that name; they
expose per-org tokens under suffixed names, so map the right one in for the
command. The runs for this repo live in the `elviskahoro` org:

```bash
env | cut -d= -f1 | grep -iE "rwx|rwc"   # list names only, never print values
# Conductor exposes RWX_ACCESS_TOKEN_ELVISKAHORO; some sandboxes use RWC_ACCESS_TOKEN_ELVISKAHORO instead.
export RWX_ACCESS_TOKEN="${RWX_ACCESS_TOKEN_ELVISKAHORO:-${RWC_ACCESS_TOKEN_ELVISKAHORO:?no elviskahoro token set}}"
rwx results <run-id>                      # run-id is the hex id in the cloud.rwx.com/elviskahoro/runs/<id> URL
rwx logs <task-id> --output /tmp/rwxlogs  # task ids are listed by `rwx results` for failed tasks
grep -rhiE 'error|ISSUES' /tmp/rwxlogs    # find the lint failures in a failed trunk-check
```

`RWX: trunk-check` runs markdownlint and markdown-table-prettify. The exact
gate needs the `trunk` binary (absent in sandboxes), but you can pre-check
markdown with `npx -y markdownlint-cli2@0.23.3 --config <.markdownlint.yaml> AGENTS.md`
(config: `configs/.markdownlint.yaml` in the `oss-linter-trunk` plugin repo,
ref in `.trunk/trunk.yaml` `plugins.sources`); `markdown-table-prettify` also
ships an npm bin. MD029 requires each ordered list to restart at 1, so do not
number continuously across subsections. Pad table columns to equal width.

- Use the `elviskahoro` token. A token for another org (e.g.
  `RWX_ACCESS_TOKEN_MARCHILI`) authenticates but returns `not found` for this
  repo's runs.
- Never echo, log, or commit the token value.
- Pullfrog GitHub Actions agents have neither the CLI nor these variables
  (credential env vars are filtered). Use GitHub commit-status metadata
  instead: `gh api repos/<owner>/<repo>/commits/<sha>/status` carries the run
  URL and failure description.
- `rwx results` prints task-level failure reasons that GitHub checks hide, e.g.
  `The vault "sdk-python-attio" is locked` when a run cannot read its secrets
  (the run fails before any task log exists). With approvals enabled on that
  vault, a non-`main` run needing its secrets instead raises an approval
  request and waits for an approver; a denial fails it. That applies to the
  main-pinned `spec-update-check.yml` and `regenerate.yml`.
  `.rwx/integration.yml` instead reads the `sdk-python-attio-it` vault (a
  throwaway sandbox key, approvals off, unlocked), so PR runs need no approver.

Full workflow, flags and per-file notes: `.agents/skills/rwx/SKILL.md`. What
the CLI can do here:

- `rwx run .rwx/<file>.yml --wait` runs CI on your uncommitted working tree (no
  commit or push); `--target <task>` limits it.
- `rwx run .rwx/pyright.yml` / `pyrefly.yml` type-check remotely, no local venv.
- `rwx results`, `rwx logs`, `rwx artifacts` inspect runs; `rwx retry` and
  `rwx cancel` manage them.
- `rwx dispatch regenerate --ref main` regenerates the SDK without Speakeasy.
- `rwx dispatch release --ref main --wait` releases the version already
  committed on `main` with no local steps (`.rwx/release.yml`; there is no
  local release script). The PyPI checks and `uvx` smoke tests run in Dagger
  (`ci/run.sh release-status|release-verify X.Y.Z`); only the tag push and the
  uploads stay in RWX, next to their vault secrets. Preflight
  (exits green once both packages have a wheel and sdist on PyPI; a partial
  upload still publishes) -> annotated `vX.Y.Z` tag
  (reused if it exists, never moved) -> the `publish.yml` chain embedded at that
  tag -> waits for both packages on PyPI and runs `uvx attio@X --version` /
  `uvx gtm-attio@X --version`. It has no bump step and never uses Speakeasy:
  bump through the regeneration pipeline first. Dispatch-only (no `cli`
  trigger). The tag push uses no PAT: a per-run token from the private GitHub
  App `rwx-automation-elviskahoro` (installed on this repo only) in the
  `sdk-python-attio-release` vault (main, approvals off). `publish.yml` has no
  tag-push trigger, so the tag leaves no stray run behind.
- `rwx dispatch publish --ref main --param tag=vX.Y.Z` publishes an already-pushed
  release tag immediately. The run checks out the tag and verifies it matches
  the committed version. `PYPI_TOKEN_ATTIO` and `PYPI_TOKEN_GTM_ATTIO` live alone in the
  `sdk-python-attio-publish` vault, one project-scoped token per distribution,
  locked to `main` and `refs/tags/v*` with approvals off. A manually pushed `v*`
  tag does not start a run; dispatch it as above.
- `rwx sandbox exec -- <cmd>` runs commands in a persistent sandbox.
- `rwx lint` validates `.rwx/*.yml`; `rwx docs search|pull` is the docs source.

### Trunk Flaky Tests uploads (`.rwx/pytest.yml`)

`pytest-run` records captain's exit code, `trunk-upload` uploads
`tmp/junit-*.xml` (including failed runs) and `pytest` re-fails on the saved
code. Uploads run on main, merge-queue, manual and `elviskahoro` PRs only.

- `TRUNK_API_TOKEN` is the org-wide Trunk token, so it lives alone in the
  `sdk-python-attio-trunk` vault (grants `elviskahoro/sdk-python-attio:**`,
  `*/*`, `:main`; approvals off; "Allow public repositories" on). Never add
  another secret to it. The repository scope of the repo-less grants is
  undocumented; `rwx vaults list` is the only way to confirm whether `*/*`
  reaches other org repos.
- The org slug (`sanhedrin`) mirrors sdk-python-linear; the collection ID
  (`xw7SIPox`) is this repo's own Trunk collection, verified by the first
  green upload.
- The trunk launcher sha256 pins only the bash bootstrap;
  `TRUNK_ANALYTICS_CLI_VERSION` in the task env pins the trunk-analytics-cli
  binary that actually runs (no tarball digest is verified either way). Bump
  both deliberately.

### RoboRev review (`.rwx/roborev.yml`)

Dispatch-only review of local work, required before publishing a PR:

```bash
rwx run .rwx/roborev.yml --wait
```

- Reviews `merge-base(origin/main, HEAD)..HEAD` (uncommitted work is committed
  inside the run) with the agent and model in `.roborev.toml` (pi + Kilo).
- Fails closed: a missing `roborev: Review Passed` line exits non-zero.
- `ROBOREV_VERSION` and its `ROBOREV_SHA256` are pinned in the workflow; bump
  both together.
- `KILO_API_KEY` lives alone in the `sdk-python-attio-roborev` vault. Never
  add another secret to it.

### Regenerating on RWX (`.rwx/regenerate.yml`)

Use this when you have no Speakeasy CLI or container runtime locally. It
regenerates, verifies, and exports the diff as an artifact; it never commits,
pushes, or opens a PR.

```bash
rwx dispatch regenerate --ref main            # add --param fetch=true to adopt the latest upstream spec
rwx artifacts download <run-id> --task patch regenerate-patch --auto-extract
git apply .rwx/downloads/<dir>/regenerate.patch
```

- Tasks: `generate` (host Speakeasy CLI, `ci/pipeline.py generate --no-fetch`,
  compile step on) -> `captain` (`rwx/install-captain 1.2.0`) -> `verify`
  (`check-overlay`, `mypy generated/src`, `captain run
  sdk-python-attio-pytest`, so retries and flake quarantine guard the suite
  instead of bare `pytest -q`) -> `patch` (allowlist check, then
  `regenerate.patch`). The patch is diffed against a pre-generation snapshot,
  so only generation output is captured.
- Secret: `SPEAKEASY_API_KEY` lives in the RWX vault `sdk-python-attio`
  (referenced as `vaults.sdk-python-attio.secrets.SPEAKEASY_API_KEY`), not the
  `default` vault. `spec-update-check.yml` reads it from that vault, so the
  scheduled run (pinned to `main`) resolves the key and regenerates on drift.
  The vault is locked to `main` with approvals enabled, so local `rwx run`
  off `main` cannot resolve the key without a vault approval — use the
  dispatch above (pinned to `main`).
- `generated/mypy.ini` is required: Speakeasy's compile step runs mypy with
  `generated/` as cwd, where the root `pyproject.toml` `[tool.mypy]` is not
  read, which otherwise fails with ~565 `import-not-found` errors. It is
  listed in `generated/.genignore` so regeneration keeps it.
- `generated/pylintrc` is hand-maintained (also in `generated/.genignore`):
  the compile step runs the root dev-group pylint (4.x), and Speakeasy's
  pylint-3 template fails it (removed `suggestion-mode` option, plus
  `too-many-positional-arguments` and `unidiomatic-typecheck` hits).
- The CLI is pinned to 1.804.0 via `speakeasyVersion` in
  `.speakeasy/workflow.yaml`, so `speakeasy run` cannot self-upgrade (it once
  promoted itself to 1.803.2); the pipeline fails the run when the host CLI
  differs from the pin.
- `tests/test_overlay_error_code_coverage.py::EXPECTED_ENDPOINTS` must list
  every endpoint `overlay.yaml` adds `validation_type` to.

### Regenerating locally: Dagger first, host CLI as fallback

`ci/pipeline.py generate` uses the pinned Speakeasy container via Dagger
whenever `SPEAKEASY_API_KEY` is set and `SPEAKEASY_USE_HOST_CLI` is not
(`_local_speakeasy_usable`). Try that first:

```bash
uv run python ci/pipeline.py generate --no-fetch
```

If the workspace cannot run Dagger (no Docker/container runtime, e.g. cloud
sandboxes; the run dies with an engine error), fall back to the host CLI by
setting `SPEAKEASY_USE_HOST_CLI=1`. This needs the `speakeasy` CLI on `PATH`
and `SPEAKEASY_API_KEY` set; no vault or RWX is needed. The flag errors out
if the CLI is missing, rather than falling back to Dagger.

```bash
ci/regenerate_host.sh            # add --fetch to adopt the latest upstream spec
```

The script installs the pinned, checksum-verified CLI if missing, runs
generation with `SPEAKEASY_USE_HOST_CLI=1`, then `uv lock`, `check-overlay`,
`mypy generated/src` and `pytest -q`. It never commits. Keep its CLI
pin/checksum in sync with `.rwx/regenerate.yml`.

- Run it on a branch cut from current `main`. An older branch may lack
  `generated/mypy.ini`, and the compile step then fails with ~565 mypy
  `import-not-found` errors.
- Use Python 3.13 (what RWX uses); put it first on `PATH` if the system
  Python differs (`uv python install 3.13`).
- Commit only `generated/`, `openapi/`, `.speakeasy/`, `pyproject.toml`,
  `uv.lock`, `README.md`, as the RWX patch allowlist does.

### Always regenerate before opening a PR

Any change to `overlay.yaml`, `ci/post_generate_patch.py`, `.speakeasy/`, or
`openapi/` MUST be accompanied by a regeneration in the same PR, with the
resulting `generated/`, `.speakeasy/`, `pyproject.toml`, `uv.lock` and
`README.md` changes committed. Overlay-only PRs that leave the SDK stale are
not acceptable: reviewers need the SDK diff next to the overlay change. When in
doubt, regenerate anyway (`ci/regenerate_host.sh`, or the Dagger path above); a
no-op run still bumps the version, which must be kept in sync across
`.speakeasy/gen.yaml`, `pyproject.toml` and `generated/src/attio/_version.py`.

### Important Notes

- The SDK is fully generated code — manual edits to `generated/src/attio/` will be overwritten on next generation.
- The overlay exists because Speakeasy infers `date` type from ISO8601 timestamp strings, but Attio returns timestamps as strings that should stay as `str` in Python.
- The `list` → `list_id` renames avoid shadowing Python's built-in `list`.
- Never add anything for backwards compatibility (no `MODEL_RENAME_ALIASES` entries for new renames, shims, or deprecated re-exports). We embrace breaking changes: when a regeneration renames or removes a public symbol, let it break and note it in the PR. The existing 0.26.1 aliases may be retired.
- Description-only spec changes (marketing copy) are reported by `check-openapi` but do not count as structural drift, so they do not trigger the automated workflow.

<!-- entire-agent:begin -->
Read .entire/agent-guide.md for this repository's workflow, source inspection, and verification guidance.
@.entire/agent-guide.md
<!-- entire-agent:end -->
