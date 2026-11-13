# ci/main.py: portable CI core (Dagger)

`pytest`, `pyright` and `pyrefly` run in Dagger containers from a plain Dagger
SDK program (no module, no `dagger.toml`/`dagger.json`). RWX stays the orchestrator.

```bash
ci/run.sh test [--junit-name NAME] [pytest args...]   # uv sync --frozen + pytest; exports tmp/ (junit, log.json)
ci/run.sh pyright [--paths "attio_cli ci"]            # pyright 1.1.414 (Trunk pin)
ci/run.sh pyrefly [--paths "attio_cli ci"]            # pyrefly 1.3.1 (Trunk pin)
ci/run.sh all
```

Prerequisites: Docker and the `dagger` CLI **0.21.10** (kept in lockstep with
`dagger-io==0.21.10` in `pyproject.toml`). Under 0.21.x the entry point is
`dagger run`; Dagger 1.x renames it (`dagger api with-session`), so update
`ci/run.sh` and `.rwx/*.yml` together if re-pinning. Dagger cannot run in
Conductor cloud sandboxes (no Docker): validate with `rwx run .rwx/<file>.yml`.

## Layers

- A (RWX, content-cached): python, uv, `sync`, `dagger-cli-install`
  (sha256-pinned, no `use:`), `dagger-engine-warm` (`docker: preserve-data`), captain.
- B (RWX): triggers, status checks, trunk-upload/pytest gate, integration, publish,
  regenerate, spec-update, trunk-check (unchanged).
- C (Dagger, `ci/main.py`): `pytest-run`, `pyright`, `pyrefly`.

Image `python:3.13-slim-bookworm`, uv `0.11.26`, uv cache in a Dagger cache volume.
`.captain/config.yml` calls `ci/run.sh test`, so Captain retries and Trunk uploads still work.

## Cache behavior

Docs-only/source-only change: `sync`, `dagger-*` tasks stay cache hits; only the
Dagger task reruns (it is `cache: false`/uncached by design). Lockfile change: `sync`
reruns. Dagger's own state is not persisted across RWX runs (no `tool-cache` export
yet), so the engine's uv/image layers are cold on each CI run.
