"""``ci/pipeline.py publish`` uploads each distribution with its own token.

PyPI project-scoped tokens cover exactly one project, so a single token can
never publish both ``attio`` and ``gtm-attio``.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

PIPELINE = Path(__file__).resolve().parent.parent / "ci" / "pipeline.py"
_spec = importlib.util.spec_from_file_location("attio_test_pipeline_publish", PIPELINE)
PIPE = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(PIPE)

TOKEN_NAMES = ("PYPI_TOKEN_ATTIO", "PYPI_TOKEN_GTM_ATTIO")


def _make_dist(root: Path) -> None:
    dist = root / "dist"
    dist.mkdir()
    for name in (
        "attio-0.28.9-py3-none-any.whl",
        "attio-0.28.9.tar.gz",
        "gtm_attio-0.28.9-py3-none-any.whl",
        "gtm_attio-0.28.9.tar.gz",
    ):
        (dist / name).write_text("x")


def test_each_distribution_uploads_with_its_own_token(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _make_dist(tmp_path)
    calls: list[list[str]] = []
    monkeypatch.setattr(PIPE.subprocess, "run", lambda argv, check: calls.append(argv))

    PIPE._publish_artifacts()

    uploads = {}
    for argv in calls:
        artifacts = argv[argv.index("--artifacts") + 1]
        token = argv[argv.index("--pypi-token") + 1]
        uploads[token] = sorted(p.name for p in (tmp_path / artifacts).iterdir())
    assert uploads == {
        "env:PYPI_TOKEN_ATTIO": ["attio-0.28.9-py3-none-any.whl", "attio-0.28.9.tar.gz"],
        "env:PYPI_TOKEN_GTM_ATTIO": [
            "gtm_attio-0.28.9-py3-none-any.whl",
            "gtm_attio-0.28.9.tar.gz",
        ],
    }


def test_missing_distribution_fails_before_any_upload(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _make_dist(tmp_path)
    for f in (tmp_path / "dist").glob("gtm_attio-*"):
        f.unlink()
    calls: list[list[str]] = []
    monkeypatch.setattr(PIPE.subprocess, "run", lambda argv, check: calls.append(argv))

    with pytest.raises(RuntimeError, match="gtm_attio"):
        PIPE._publish_artifacts()
    assert calls == []


@pytest.mark.parametrize("missing", TOKEN_NAMES)
def test_publish_requires_both_tokens(monkeypatch, missing) -> None:
    for name in TOKEN_NAMES:
        monkeypatch.setenv(name, "set")
    monkeypatch.delenv(missing)
    with pytest.raises(RuntimeError, match=missing):
        PIPE._require_publish_tokens()
