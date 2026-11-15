"""Unit tests for ci/pypi_release_status.py, the release workflow's PyPI check."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "ci" / "pypi_release_status.py"
_spec = importlib.util.spec_from_file_location("pypi_release_status", SCRIPT)
assert _spec and _spec.loader
status = importlib.util.module_from_spec(_spec)
sys.modules["pypi_release_status"] = status
_spec.loader.exec_module(status)

WHEEL = {"packagetype": "bdist_wheel"}
SDIST = {"packagetype": "sdist"}


def _fetcher(releases: dict[str, list[dict] | None]):
    def fetch(url: str) -> dict | None:
        package = url.split("/pypi/")[1].split("/")[0]
        files = releases[package]
        return None if files is None else {"urls": files}

    return fetch


def test_complete_release_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    fetch = _fetcher({"attio": [WHEEL, SDIST], "gtm-attio": [SDIST, WHEEL]})
    assert status.main(["1.2.3"], fetch) == 0
    assert "gtm-attio==1.2.3: wheel and sdist are on PyPI" in capsys.readouterr().out


def test_missing_release_exits_one(capsys: pytest.CaptureFixture[str]) -> None:
    fetch = _fetcher({"attio": None, "gtm-attio": None})
    assert status.main(["1.2.3"], fetch) == 1
    assert "attio==1.2.3: not on PyPI" in capsys.readouterr().out


def test_partial_upload_is_not_published(capsys: pytest.CaptureFixture[str]) -> None:
    """Both version endpoints answer 200, but gtm-attio lacks its sdist."""
    fetch = _fetcher({"attio": [WHEEL, SDIST], "gtm-attio": [WHEEL]})
    assert status.main(["1.2.3"], fetch) == 1
    assert "gtm-attio==1.2.3: incomplete, missing sdist" in capsys.readouterr().out


def test_unreadable_pypi_exits_two() -> None:
    def fetch(url: str) -> dict | None:
        raise OSError("connection reset")

    assert status.main(["1.2.3"], fetch) == 2


def test_requires_exactly_one_version_argument() -> None:
    assert status.main([]) == 2
