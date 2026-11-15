"""Report whether a version of attio and gtm-attio is fully published on PyPI.

Usage: python3 ci/pypi_release_status.py X.Y.Z

Each distribution ships a wheel and an sdist, so a version only counts as
published when PyPI lists both for both packages. A partial upload (one file
landed, the next failed) must not look published, or .rwx/release.yml would
skip the upload that finishes it.

Exit codes: 0 complete, 1 missing or incomplete, 2 PyPI could not be read.
Stdlib only: .rwx/release.yml runs it before any dependencies are installed.
"""

# ruff: noqa: INP001

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from collections.abc import Callable
from http import HTTPStatus

PACKAGES = ("attio", "gtm-attio")
REQUIRED_TYPES = frozenset({"bdist_wheel", "sdist"})
PYPI_JSON = "https://pypi.org/pypi/{package}/{version}/json"

Fetch = Callable[[str], "dict | None"]


def fetch_release(url: str) -> dict | None:
    """Return PyPI's JSON for a release, or None when it does not exist."""
    try:
        # Always the fixed https PyPI URL built from PYPI_JSON, never file://.
        with urllib.request.urlopen(url, timeout=30) as response:  # noqa: S310  # nosec B310  # nosemgrep: python.lang.security.audit.dynamic-urllib-use-detected.dynamic-urllib-use-detected
            return json.load(response)
    except urllib.error.HTTPError as exc:
        if exc.code == HTTPStatus.NOT_FOUND:
            return None
        raise


def missing_types(package: str, version: str, fetch: Fetch = fetch_release) -> set[str]:
    """Required artifact types PyPI does not list yet for package==version."""
    release = fetch(PYPI_JSON.format(package=package, version=version))
    if release is None:
        return set(REQUIRED_TYPES)
    present = {file["packagetype"] for file in release.get("urls", [])}
    return set(REQUIRED_TYPES - present)


def main(argv: list[str], fetch: Fetch = fetch_release) -> int:
    if len(argv) != 1:
        print("usage: pypi_release_status.py X.Y.Z", file=sys.stderr)
        return 2
    (version,) = argv
    complete = True
    for package in PACKAGES:
        try:
            missing = missing_types(package, version, fetch)
        except (OSError, ValueError) as exc:
            print(
                f"Could not read PyPI for {package}=={version}: {exc}",
                file=sys.stderr,
            )
            return 2
        if not missing:
            print(f"{package}=={version}: wheel and sdist are on PyPI")
        elif missing == REQUIRED_TYPES:
            print(f"{package}=={version}: not on PyPI")
            complete = False
        else:
            print(
                f"{package}=={version}: incomplete, missing {', '.join(sorted(missing))}",
            )
            complete = False
    return 0 if complete else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
