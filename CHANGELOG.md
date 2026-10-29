# Changelog

## Unreleased — 2026-10-05

Expands the standalone `uvx gtm-attio` CLI with safe people search/add/update,
company search/add/update, and note list/add/update commands. Mutations write
immediately, validate JSON inputs, and return the versioned reliability
envelope; search and list results are returned in `meta.results`.

Regenerates the SDK (0.26.2) from the committed spec and overlay. Three
public model names are renamed by the error-code union flattening, and the old
names are kept as aliases (`ci/post_generate_patch.py`, `MODEL_RENAME_ALIASES`)
so existing imports keep working; prefer the new names:

- `PostV2ActivitiesActivityRecordsForbiddenCodeUnion` (+ `TypedDict`) →
  `PostV2ActivitiesActivityRecordsCodeUnion` (+ `TypedDict`)
- `PutV2ActivitiesActivityRecordsForbiddenCodeUnion` (+ `TypedDict`) →
  `PutV2ActivitiesActivityRecordsCodeUnion` (+ `TypedDict`)
- `PutV2ListsListEntriesCodeMultipleMatchResults` → `CodeMultipleMatchResults`

Regenerates the SDK (0.26.3) against the unchanged spec — a content-empty
bump that keeps `pyproject.toml`, `uv.lock`, and the Speakeasy-side version
files in lockstep.

Regenerates the SDK (0.26.4) against the unchanged spec. No model or
API-surface changes — the generator bump (Speakeasy 1.804.0, template
2.952.5) lands the upstream empty-string early-return for security-scheme
values in `generated/src/attio/utils/security.py`, and `pyproject.toml`,
`uv.lock`, and the Speakeasy-side version files stay in lockstep.

Regenerates the SDK (0.26.5) against the unchanged spec — the overlay's
`value` targets moved to RFC 9535 bracket notation; no model or API-surface
changes.

Regenerates the SDK (0.27.0) against the pinned 2026-10-26 spec and repairs
the overlay for upstream error-code drift: the lists-entries POST 400 `code`
anyOf is flattened and the activity-record POST/PUT 400 enums gain the
missing codes, so the record and entry write endpoints now accept
`duplicate_values`, `limit_reached`, and `multiple_match_results` 400 codes.
**Breaking changes** (the 0.x minor bump is the signal; 0.26.2–0.26.7 were
never published, so 0.27.0 is the first release after 0.26.1) — 50 exports
that shipped in 0.26.1 are renamed or removed, without aliases:

- **32 `attio.errors` exports rename** across the eight record write
  endpoints (`Post`/`Put` `...Records` and `Put`/`Patch`
  `...Records/{record_id}`, for both objects and activities):
  `...InvalidRequestError(Data)` → `...BadRequestInvalidRequestError(Data)`
  (400) and `...ConcurrentWriteConflictError(Data)` →
  `...ConflictInvalidRequestError(Data)` (409).
- **8 `attio.models` exports split by status**: `...RecordIDCodeUnion` and
  `...RecordIDCodeUnionTypedDict` for the four `{record_id}` PUT/PATCH
  endpoints became `...BadRequestCodeUnion` / `...ConflictCodeUnion` pairs.
- **9 `attio.models` exports collapse** into the flat `...BadRequestCode`
  Literals: `Post`/`Put` `V2ActivitiesActivityRecords`
  `BadRequestCodeUnion` (+ `TypedDict`), `...CodeValueNotFound`,
  `...CodeParticleGateViolation`, and
  `CodeMatchingAttributeDefinitionNotUnique`.
- **`PostV2SQLType` is removed** (SQL request models reshaped) — struct
  parameter values are now free-form (`Dict[str, Any]`) so nested
  `type`/`value` pairs survive serialization (#106);
  `PostV2SQLBadRequestType` is new for 400 responses.

Regenerates the SDK (0.27.3) against the unchanged spec. No model or
API-surface changes: the pinned Speakeasy 1.800.1 emits generator template
2.943.0 (down from 2.952.5), so `ci/post_generate_patch.py` now restores the
empty-string guard in `utils/security.py` and the `_DURATION_ADAPTER` annotation in
`utils/datetimes.py` after every regeneration (#117).
Adds a test pinning the activity-record 403 `ForbiddenCodeUnion` names (#88).

## 0.25.1 — 2026-10-03

Adopts Attio's 2026-10-03 OpenAPI spec and repairs the Speakeasy overlay.
**Breaking changes** (the 0.x minor bump is the signal):

- **Input `values` move from `datetime.date` to `str`.** Timestamp values
  on activity records, `PUT .../attributes/{attribute}/values` endpoints,
  and the `input-value` component previously generated as `date` — which
  rejected the ISO 8601 strings Attio actually returns and forced callers
  to pass `datetime.date` objects. They are now `str`. Callers passing
  `datetime.date` must switch to Attio's timestamp strings
  (e.g. `"2023-01-02T13:00:00.000000000Z"`).
- **`GET /v2/self` active tokens now require `token_level`**
  (`"workspace"` or `"user"`): hand-built `AttioCom` / `AttioComTypedDict`
  payloads without it fail validation. Parse the field from the response
  instead of constructing payloads literally.
- **Five public model exports are removed** by the error-code union
  flattening: `CodeMultipleMatchResults`,
  `PutV2ObjectsObjectRecordsCodeMergeInProgress`,
  `PutV2ObjectsObjectRecordsCodeUnion`,
  `PutV2ObjectsObjectRecordsCodeUnionTypedDict`, and
  `PutV2ObjectsObjectRecordsCodeValueNotFound` — all replaced by the
  consolidated single-enum Literals (which now also accept
  `validation_type`, `particle_gate_violation`, and
  `concurrent_write_conflict` where the API returns them).

New API surface from the spec: `DELETE`/`PATCH`/`PUT`
`/v2/meetings/{meeting_id}` and `PUT /v2/activities/{activity}/records`
(upsert), plus 409 conflict responses on write endpoints.

Tooling: weekly spec-drift detection (`ci/spec_diff.py`,
`ci/pipeline.py check-openapi`, `.rwx/spec-update-check.yml`)
with an overlay-health gate on generation; release scripts moved under
`ci/` behind generator-proof wrappers.
