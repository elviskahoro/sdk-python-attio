"""Keep README examples runnable: agents copy them verbatim."""

from __future__ import annotations

import re
import shlex
from pathlib import Path

import pytest

from attio import SDK
from attio_cli import main as cli_main

REPO_ROOT = Path(__file__).resolve().parent.parent
README = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
REPO_BLOB_URL = re.compile(
    r"https://github\.com/elviskahoro/sdk-python-attio/(?:blob|tree)/main/([^)#\s]+)",
)


def _fenced_blocks(language: str) -> list[str]:
    return re.findall(rf"^```{language}\n(.*?)^```$", README, re.MULTILINE | re.DOTALL)


def _cli_examples() -> list[str]:
    commands = []
    for block in _fenced_blocks("bash"):
        for line in block.replace("\\\n", " ").splitlines():
            if line.startswith(("uvx gtm-attio ", "uvx attio ")):
                commands.append(line)
    return commands


PYTHON_BLOCKS = _fenced_blocks("python")


@pytest.mark.parametrize(
    "block",
    PYTHON_BLOCKS,
    ids=[f"python-block-{i}" for i in range(len(PYTHON_BLOCKS))],
)
def test_python_examples_compile(block: str) -> None:
    compile(block, "README.md", "exec")


def test_sdk_methods_in_examples_exist() -> None:
    sdk = SDK(oauth2="placeholder")
    calls = set(re.findall(r"\bsdk\.(\w+)\.(\w+)\(", README))
    assert calls
    missing = sorted(
        f"sdk.{resource}.{method}"
        for resource, method in calls
        if not hasattr(getattr(sdk, resource, None), method)
    )
    assert not missing, f"README references SDK methods that do not exist: {missing}"


@pytest.mark.parametrize("command", _cli_examples())
def test_cli_examples_parse(command: str) -> None:
    argv = shlex.split(command)[2:]
    cli_main._parser().parse_args(argv)


def test_cli_examples_cover_every_resource() -> None:
    resources = {shlex.split(command)[2] for command in _cli_examples()}
    assert resources == {"people", "companies", "notes"}


def test_no_unrendered_placeholders_or_relative_doc_links() -> None:
    assert "<UNSET>" not in README
    assert "](docs/" not in README
    assert "](./generated/" not in README


def test_repository_links_point_at_existing_paths() -> None:
    paths = set(REPO_BLOB_URL.findall(README))
    assert paths
    missing = sorted(path for path in paths if not (REPO_ROOT / path).exists())
    assert not missing, f"README links to paths missing from the repo: {missing}"
