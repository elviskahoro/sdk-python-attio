# Changelog

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
`ci/pipeline.py check-openapi`, `.github/workflows/spec-update-check.yml`)
with an overlay-health gate on generation; release scripts moved under
`ci/` behind generator-proof wrappers.
