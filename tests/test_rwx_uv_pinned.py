"""Every .rwx workflow's ``uv`` task must pin uv to one exact version."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

WORKFLOWS = sorted((Path(__file__).resolve().parent.parent / ".rwx").glob("*.yml"))
PIN = re.compile(r"pip install uv==(\d+(?:\.\d+)+)(?:\s|$)")


def _uv_run(path: Path) -> str:
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    tasks = {t.get("key"): t for t in doc["tasks"]}
    assert "uv" in tasks, f"{path.name} has no `uv` task"
    return str(tasks["uv"].get("run", ""))


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.name)
def test_uv_task_pins_exact_version(path: Path) -> None:
    assert PIN.search(_uv_run(path)), f"{path.name}: `uv` task must run `pip install uv==X.Y.Z`"


def test_all_workflows_pin_same_uv_version() -> None:
    versions = {p.name: PIN.search(_uv_run(p)).group(1) for p in WORKFLOWS}  # type: ignore[union-attr]
    assert len(set(versions.values())) == 1, versions
