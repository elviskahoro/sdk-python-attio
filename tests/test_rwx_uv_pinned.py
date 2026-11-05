"""Every .rwx workflow's ``uv`` task must pin uv to one exact version."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

WORKFLOWS = sorted((Path(__file__).resolve().parent.parent / ".rwx").glob("*.y*ml"))
# Every `pip install ... uv` occurrence must carry its own exact pin: an
# unpinned fallback (`pip install uv==X || pip install uv`) installs latest.
INSTALL = re.compile(r"pip install (?:-[\w=-]+ )*uv(==\d+(?:\.\d+)+)?(?=\s|$)")


def _uv_run(path: Path) -> str:
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    tasks = {t.get("key"): t for t in doc["tasks"]}
    assert "uv" in tasks, f"{path.name} has no `uv` task"
    return str(tasks["uv"].get("run", ""))


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.name)
def test_uv_task_pins_exact_version(path: Path) -> None:
    pins = INSTALL.findall(_uv_run(path))
    assert pins, f"{path.name}: `uv` task must run `pip install uv==X.Y.Z`"
    assert all(pins), f"{path.name}: unpinned `pip install uv` alongside the pin"


def test_all_workflows_pin_same_uv_version() -> None:
    versions = {
        p.name: {v.lstrip("=") for v in INSTALL.findall(_uv_run(p))} for p in WORKFLOWS
    }
    assert len({v for vs in versions.values() for v in vs}) == 1, versions
