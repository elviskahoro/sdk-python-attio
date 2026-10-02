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

1. **Fetch the latest spec** (if not already done):

   ```bash
   dagger run python ci/pipeline.py fetch-openapi
   ```

   This downloads from `https://api.attio.com/openapi/api`, saves it with a timestamp, and updates `workflow.yaml`.

2. **Diff the new spec against the previous one** to understand what changed:

   ```bash
   # Compare endpoint counts
   python3 -c "import json; old=json.load(open('openapi/api-OLD.json')); new=json.load(open('openapi/api-NEW.json')); print(f'Old paths: {len(old[\"paths\"])}'); print(f'New paths: {len(new[\"paths\"])}')"

   # List new/removed endpoints
   python3 -c "
   import json
   old = set(json.load(open('openapi/api-OLD.json'))['paths'].keys())
   new = set(json.load(open('openapi/api-NEW.json'))['paths'].keys())
   added = new - old
   removed = old - new
   if added: print('Added:', *sorted(added), sep='\n  ')
   if removed: print('Removed:', *sorted(removed), sep='\n  ')
   if not added and not removed: print('No endpoint changes')
   "
   ```

3. **Verify the overlay still applies cleanly**. The overlay uses JSONPath targets that reference specific `oneOf` indices (e.g., `oneOf[16]`). If the spec schema changed, these indices may have shifted. Check:
   - Do `oneOf[16]` entries still correspond to timestamp value types?
   - Are there new endpoints with timestamp values that need overlay entries?
   - Do the `list` parameter rename targets still match?

4. **Update the overlay if needed**. If indices shifted or new endpoints were added, update `overlay.yaml` accordingly. Refer to `overlay_guide.md` for syntax and patterns.

5. **Run Speakeasy generation**:

   ```bash
   speakeasy run
   ```

   `speakeasy run` rewrites `src/` and drops manual patches that `overlay.yaml`
   cannot express. Re-apply them so the regenerated tree keeps the GET /v2/self
   `active` value discriminators (the pipeline does this automatically; for a
   direct `speakeasy run`, run `python ci/post_generate_patch.py` after).

6. **Review generated changes**:
   - Check `git diff` for new/modified SDK methods in `src/attio/`
   - Verify new models in `src/attio/models/`
   - Check for any type errors: `uv run mypy src/`
   - Ensure the package still builds: `uv build`

7. **Update the version** in `.speakeasy/gen.yaml` (`python.version`) and verify it matches `pyproject.toml`.

### Important Notes

- The SDK is fully generated code — manual edits to `src/attio/` will be overwritten on next generation.
- The overlay exists because Speakeasy infers `date` type from ISO8601 timestamp strings, but Attio returns timestamps as strings that should stay as `str` in Python.
- The `list` → `list_id` renames avoid shadowing Python's built-in `list`.
