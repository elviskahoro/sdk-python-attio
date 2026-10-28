# Attio SDK Python

## Beads Issue Tracking

- This repository uses Beads with the DoltHub remote `elviskahoro/sdk-python-attio`.
- Use `bd prime` for the current workflow context, `bd ready` to find unblocked work, and `bd create`/`bd update`/`bd close` for issue changes.
- Pull remote changes explicitly with `bd dolt pull`; push committed Dolt changes with `bd dolt push`.
- Authenticate locally with `DOLT_REMOTE_USER` and `DOLT_REMOTE_PASSWORD`; never commit credentials or `.beads` runtime/database files.

## Git Workflow

- Commits are allowed when the user explicitly asks to commit
- Always show the user what will be committed before committing
- Do NOT push to remote unless explicitly asked

## Landing PRs

PRs land through the Trunk Merge Queue, not the GitHub Merge button.

- Submit: `trunk merge <pr-number>` (a number, not a URL or branch name).
- Check once: `trunk merge status <pr-number>`. States: Queued, Testing,
  Tests Passed, Merged. Report the state and stop. Never poll in a loop.
- Never use `gh pr merge` or the GitHub Merge button. They bypass the queue.
- Never use `--force`, `pause` or `resume`.
- Leave priority at the default (`medium`). `urgent` and `high` are for
  incidents and need an explicit reason from the user.
- Failed or PENDING_FAILURE: PENDING_FAILURE may be a flake, so retry once.
  Failed means push a fix to the PR branch and resubmit. Do not resubmit
  blindly in a loop.
- Auth failure: run `trunk login` once and retry.
- Refuse to queue from main or a protected branch.
- A `Closes #N` line in the PR body auto-closes the issue when the queue lands
  the PR. Do not close the issue by hand beforehand.

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
   `generated/src/attio/models/get_v2_selfop.py`, the `scripts/publish.sh` and
   `scripts/release.sh` wrappers, the standalone CLI entry point/docs in
   `pyproject.toml` and `README.md`, SDKHooks `init_hooks` wiring plus
   the hooks-package re-export in `generated/src/attio/_hooks/sdkhooks.py` and
   `generated/src/attio/_hooks/__init__.py`, the 0.26.1 model rename
   aliases in `generated/src/attio/models/__init__.py` and the renamed
   activity/list operation modules, and the unused `OpenEnumMeta` metaclass
   removal from `generated/src/attio/utils/enums.py` and
   `generated/src/attio/utils/__init__.py`). Drop `--no-fetch` to also
   adopt a freshly fetched spec. Note the Dagger path exports only `generated/`
   back to the host — docs/, README, pyproject and USAGE refresh on the
   host-CLI path (the default) — and it logs that when chosen.

6. **Review generated changes**:
   - Check `git diff` for new/modified SDK methods in `generated/src/attio/`
   - Verify new models in `generated/src/attio/models/`
   - Check for any type errors: `uv run mypy generated/src/ attio_cli/`
   - Run tests: `uv run pytest -q`
   - Ensure the package still builds: `uv build`
   - Confirm `pyproject.toml`'s dev group still contains `dagger-io`,
     `pytest`, `pytest-asyncio` — speakeasy rewrites `pyproject.toml` from
     `.speakeasy/gen.yaml`, and they only survive because they are declared
     in `gen.yaml` `python.additionalDependencies.dev`. If they vanish,
     restore them and run `uv lock && uv sync`.

7. **Verify the version** in `.speakeasy/gen.yaml` (`python.version`) matches
   `pyproject.toml` and `generated/src/attio/_version.py` (speakeasy auto-bumps the
   patch version on each regeneration with changes).

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
  compile step on) -> `verify` (`check-overlay`, `mypy generated/src`,
  `pytest -q`) -> `patch` (allowlist check, then `regenerate.patch`). The
  patch is diffed against a pre-generation snapshot, so only generation
  output is captured.
- Secret: `SPEAKEASY_API_KEY` lives in the RWX vault `sdk-python-attio`
  (referenced as `vaults.sdk-python-attio.secrets.SPEAKEASY_API_KEY`), not the
  `default` vault. `spec-update-check.yml` still reads the default vault, so
  its regeneration step is skipped until it is pointed at the new vault. The
  vault is locked to `main`, so local `rwx run` is refused (use the dispatch above).
- `generated/mypy.ini` is required: Speakeasy's compile step runs mypy with
  `generated/` as cwd, where the root `pyproject.toml` `[tool.mypy]` is not
  read, which otherwise fails with ~565 `import-not-found` errors. It is
  listed in `generated/.genignore` so regeneration keeps it.
- The CLI is pinned to 1.800.1 but Speakeasy may self-upgrade (seen: 1.803.2);
  the pipeline only warns on the mismatch.
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

### Important Notes

- The SDK is fully generated code — manual edits to `generated/src/attio/` will be overwritten on next generation.
- The overlay exists because Speakeasy infers `date` type from ISO8601 timestamp strings, but Attio returns timestamps as strings that should stay as `str` in Python.
- The `list` → `list_id` renames avoid shadowing Python's built-in `list`.
- A regeneration that renames a public model symbol which already shipped must keep the old name importable: add it to `MODEL_RENAME_ALIASES` in `ci/post_generate_patch.py` (0.26.1 precedent: the activity-record `ForbiddenCodeUnion` names became `CodeUnion`, and `PutV2ListsListEntriesCodeMultipleMatchResults` became `CodeMultipleMatchResults`) so a patch release never breaks `from attio.models import <old>` or the per-module import; retire the aliases only in a major release.
- Description-only spec changes (marketing copy) are reported by `check-openapi` but do not count as structural drift, so they do not trigger the automated workflow.

<!-- entire-agent:begin -->
Read .entire/agent-guide.md for this repository's workflow, source inspection, and verification guidance.
@.entire/agent-guide.md
<!-- entire-agent:end -->
