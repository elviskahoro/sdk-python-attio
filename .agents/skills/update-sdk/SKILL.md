---
name: update-sdk
description: Update the Attio Python SDK by fetching the latest OpenAPI spec from https://api.attio.com/openapi/api, verifying overlays, and regenerating with Speakeasy
disable-model-invocation: true
allowed-tools: Read, Grep, Glob, Bash
---

# Update SDK with Latest OpenAPI Spec

Follow these steps to update the Attio Python SDK to the latest OpenAPI spec.

## Prerequisites

- `dagger` CLI installed
- `speakeasy` CLI installed (`brew install speakeasy-api/homebrew-tap/speakeasy`)

## Steps

### 1. Fetch the latest OpenAPI spec

Run the Dagger pipeline which downloads the spec and updates `workflow.yaml`:

```bash
dagger run python ci/pipeline.py fetch-openapi
```

This will:
- Download the latest spec from https://api.attio.com/openapi/api
- Save it to `openapi/api-<YYYYMMDDHHMM>.json`
- Update `.speakeasy/workflow.yaml` to point to the new spec file

### 2. Review the new spec for breaking changes

Compare the new spec against the previous one to understand what changed:

```bash
diff openapi/api-<OLD_TIMESTAMP>.json openapi/api-<NEW_TIMESTAMP>.json
```

Pay attention to:
- New or removed endpoints
- Changed request/response schemas
- Modified parameter names or types

### 3. Verify overlay targets still apply

The `overlay.yaml` file patches the spec before generation. It currently handles:
- **Timestamp value fields**: Removes `format` fields and changes examples/descriptions so Speakeasy generates `str` instead of `date` types
- **`list` parameter renaming**: Renames `list` to `list_id` via `x-speakeasy-name-override` to avoid Python built-in conflicts

If Attio added new endpoints or changed schema indices (e.g. the `oneOf[16]` positions), the overlay targets may need updating. Check that overlay targets still resolve against the new spec.

### 4. Regenerate the SDK

```bash
speakeasy run
```

This applies the overlay to the spec and regenerates all SDK code under `src/attio/`.

`speakeasy run` rewrites `src/` from scratch, so it drops the manual patches
that `overlay.yaml` cannot express, e.g. the GET /v2/self `active` value
discriminators on `AttioCom` and `ResponseBody` in
`src/attio/models/get_v2_selfop.py`, the `scripts/publish.sh` and
`scripts/release.sh` wrappers, the standalone CLI entry point/docs in
`pyproject.toml` and `README.md`, and the SDKHooks `init_hooks` wiring and
hooks-package re-export in `src/attio/_hooks/sdkhooks.py` and
`src/attio/_hooks/__init__.py`. Re-apply them right after regenerating so the
tree the tests run against carries the invariant:

```bash
python ci/post_generate_patch.py
```

`python ci/pipeline.py generate` and `python ci/pipeline.py ci` run this patch
automatically after generation. Run it manually only after a direct
`speakeasy run`. The patch is idempotent and fails loudly if the generated
layout drifts, so a regeneration can no longer silently drop the invariant.

### 5. Review generated changes

Check what changed in the generated code:

```bash
git diff src/attio/
git diff docs/
```

Look for:
- New or removed operation methods
- Changed model types
- Any unexpected type changes (especially timestamp fields reverting to `date`)

### 6. Run tests

```bash
uv run pytest
```

### 7. Update version if needed

The SDK version is in `.speakeasy/gen.yaml` under `python.version`. Speakeasy may bump this automatically, or you can set it manually.

### 8. Clean up old spec files

Optionally remove the old spec file from `openapi/` once you've confirmed the new one works.

## Key files

| File | Purpose |
|------|---------|
| `ci/pipeline.py` | Dagger pipeline with fetch-openapi, generate, and publish commands |
| `.speakeasy/workflow.yaml` | Points Speakeasy to the input spec and overlay |
| `.speakeasy/gen.yaml` | SDK generation config (version, package name, etc.) |
| `overlay.yaml` | Patches applied to the spec before generation |
| `openapi/` | Directory containing downloaded spec files |
| `.speakeasy/gen.lock` | Tracks all Speakeasy-managed files |

## Troubleshooting

- **Overlay targets fail**: The `oneOf` indices in `overlay.yaml` are positional. If Attio reorders their schema union types, you'll need to update the index numbers.
- **New `list` parameters**: If Attio adds new endpoints that take a `list` path/query parameter, add corresponding overlay entries to rename them to `list_id`.
- **Timestamp fields typed as `date`**: If new timestamp fields appear, add overlay entries to strip their `format` and update examples/descriptions.
