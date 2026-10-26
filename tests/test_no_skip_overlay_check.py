"""CI config must never reference the overlay-gate escape hatch."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PATTERN = re.compile(r"SKIP_OVERLAY_CHECK|skip-overlay-check")


def test_ci_config_does_not_skip_overlay_check() -> None:
    offenders = []
    for d in (".rwx", ".github/workflows"):
        for f in sorted((ROOT / d).glob("*.y*ml")):
            for n, line in enumerate(f.read_text().splitlines(), 1):
                # the guard in spec-update-check.yml only *reads* the variable
                if PATTERN.search(line) and "${SKIP_OVERLAY_CHECK:-}" not in line and "forbidden" not in line:
                    offenders.append(f"{f.relative_to(ROOT)}:{n}")
    assert not offenders, offenders
