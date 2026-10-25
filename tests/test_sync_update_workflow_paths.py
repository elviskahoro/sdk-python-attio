"""Tests for the read/write anchoring of ``_sync_update_workflow`` in
``ci/pipeline.py``.

The function adopts a freshly-fetched spec into ``.speakeasy/workflow.yaml``.
Its read was already anchored to the repo root, but its write used to be
cwd-relative — so a pipeline invoked from another directory would either
crash (the cwd has no ``.speakeasy/``) or silently update the wrong file
(the cwd has its own ``.speakeasy/workflow.yaml``). These tests pin the
invariant that both the read and the write go through ``_WORKFLOW_YAML``,
the same anchor the gate's snapshot/restore uses, so the adoption touches
the repo's ``workflow.yaml`` regardless of the invocation directory.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
PIPELINE = REPO_ROOT / "ci" / "pipeline.py"


def _load_pipeline_module():
    # Load by path (like the pipeline itself does) rather than inserting
    # ci/ into sys.path, which would cache a second copy of the module
    # under a different name and split monkeypatching across copies.
    spec = importlib.util.spec_from_file_location(
        "attio_test_pipeline_paths", PIPELINE
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PIPE = _load_pipeline_module()


def _seed_workflow(repo_wf: Path, *, body: str) -> None:
    repo_wf.parent.mkdir(parents=True, exist_ok=True)
    repo_wf.write_text(body, encoding="utf-8")


def test_sync_update_workflow_writes_repo_workflow_not_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The silent-wrong-write topology: the cwd has its own
    ``.speakeasy/workflow.yaml`` so the buggy cwd-relative write would
    succeed against the cwd's file, leaving the repo's untouched."""
    repo = tmp_path / "repo"
    repo_wf = repo / ".speakeasy" / "workflow.yaml"
    _seed_workflow(repo_wf, body="location: openapi/api-000.json\n")
    monkeypatch.setattr(PIPE, "_REPO_ROOT", repo)
    monkeypatch.setattr(PIPE, "_WORKFLOW_YAML", repo_wf)

    elsewhere = tmp_path / "elsewhere"
    cwd_wf = elsewhere / ".speakeasy" / "workflow.yaml"
    _seed_workflow(cwd_wf, body="location: openapi/api-000.json\n")

    monkeypatch.chdir(elsewhere)  # cwd != _REPO_ROOT -- the bug topology
    PIPE._sync_update_workflow("openapi/api-111-overlay.json", "openapi/api-111.json")

    assert "location: openapi/api-111.json" in repo_wf.read_text(encoding="utf-8"), (
        "repo workflow.yaml should be rewritten (anchored write)"
    )
    assert cwd_wf.read_text(encoding="utf-8") == "location: openapi/api-000.json\n", (
        "cwd workflow.yaml must NOT be rewritten by an anchored implementation"
    )


def test_sync_update_workflow_does_not_crash_when_cwd_lacks_speakeasy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The loud-crash topology: the cwd has no ``.speakeasy/`` at all, so
    the buggy cwd-relative write would raise ``FileNotFoundError``. The
    anchored write must succeed against the repo's file instead."""
    repo = tmp_path / "repo"
    repo_wf = repo / ".speakeasy" / "workflow.yaml"
    _seed_workflow(repo_wf, body="location: openapi/api-000.json\n")
    monkeypatch.setattr(PIPE, "_REPO_ROOT", repo)
    monkeypatch.setattr(PIPE, "_WORKFLOW_YAML", repo_wf)

    bare_cwd = tmp_path / "bare"
    bare_cwd.mkdir(parents=True)
    assert not (bare_cwd / ".speakeasy").exists()
    monkeypatch.chdir(bare_cwd)

    PIPE._sync_update_workflow("openapi/api-222-overlay.json", "openapi/api-222.json")

    assert "location: openapi/api-222.json" in repo_wf.read_text(encoding="utf-8")
