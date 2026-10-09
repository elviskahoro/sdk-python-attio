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

## SDK Update Guide

This SDK is generated using Speakeasy from an OpenAPI spec.

### Key Files

- **SDK Generator**: Speakeasy (https://www.speakeasy.com/)
- **OpenAPI specs**: stored in `openapi/` directory, named `api-YYYYMMDDHHMM.json`
- **Overlay**: `overlay.yaml` applies targeted fixes to the spec before generation (timestamp format fixes, `list` → `list_id` parameter renames)
- **Workflow config**: `.speakeasy/workflow.yaml` defines the generation pipeline
- **Generation config**: `.speakeasy/gen.yaml` has Speakeasy settings (Python target, async mode, package name, etc.)

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

   The scheduled `.github/workflows/spec-update-check.yml` workflow runs this
   check weekly (Mondays 09:00 UTC). On drift it regenerates, runs pytest,
   and opens a PR (needs the `SPEAKEASY_API_KEY` repo secret); without the
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
   `ci/post_generate_patch.py` (the GET /v2/self `active` value
   discriminators and the `scripts/` wrappers). Drop `--no-fetch` to also
   adopt a freshly fetched spec. Note the Dagger path exports only `src/`
   back to the host — docs/, README, pyproject and USAGE refresh on the
   host-CLI path (the default) — and it logs that when chosen.

6. **Review generated changes**:
   - Check `git diff` for new/modified SDK methods in `src/attio/`
   - Verify new models in `src/attio/models/`
   - Check for any type errors: `uv run mypy src/`
   - Run tests: `uv run pytest -q`
   - Ensure the package still builds: `uv build`
   - Confirm `pyproject.toml`'s dev group still contains `dagger-io`,
     `pytest`, `pytest-asyncio` — speakeasy rewrites `pyproject.toml` from
     `.speakeasy/gen.yaml`, and they only survive because they are declared
     in `gen.yaml` `python.additionalDependencies.dev`. If they vanish,
     restore them and run `uv lock && uv sync`.

7. **Verify the version** in `.speakeasy/gen.yaml` (`python.version`) matches
   `pyproject.toml` and `src/attio/_version.py` (speakeasy auto-bumps the
   patch version on each regeneration with changes).

### Important Notes

- The SDK is fully generated code — manual edits to `src/attio/` will be overwritten on next generation.
- The overlay exists because Speakeasy infers `date` type from ISO8601 timestamp strings, but Attio returns timestamps as strings that should stay as `str` in Python.
- The `list` → `list_id` renames avoid shadowing Python's built-in `list`.
- Description-only spec changes (marketing copy) are reported by `check-openapi` but do not count as structural drift, so they do not trigger the automated workflow.

<!-- entire-graph:begin -->
This repo has the entire-graph code graph installed. Before exploring code with
grep/find/whole-file reads, read .entire/graph-agent.md — resolution-first guidance
for using graph retrieval, focused source inspection, and verification.
@.entire/graph-agent.md
<!-- entire-graph:end -->
