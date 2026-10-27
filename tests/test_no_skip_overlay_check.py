"""CI config must never reference the overlay-gate escape hatch."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PATTERN = re.compile(r"SKIP_OVERLAY_CHECK|skip-overlay-check")
GUARD_FILE = ROOT / ".rwx" / "spec-update-check.yml"

# The only permitted mentions are the guard's own two lines, matched exactly
# rather than by substring: the guard reads the variable precisely to reject
# it, and pinning its exact text means deleting or rewording it fails this
# test instead of silently shrinking the lint's coverage.
GUARD_LINES = (
    'case "${SKIP_OVERLAY_CHECK:-}" in',
    '*) echo "SKIP_OVERLAY_CHECK is forbidden in this workflow" >&2; exit 1 ;;',
)


def test_ci_config_does_not_skip_overlay_check() -> None:
    offenders = []
    guard_seen = set()
    for d in (".rwx", ".github/workflows"):
        for f in sorted((ROOT / d).glob("*.y*ml")):
            for n, line in enumerate(f.read_text().splitlines(), 1):
                if not PATTERN.search(line):
                    continue
                if f == GUARD_FILE and line.strip() in GUARD_LINES:
                    guard_seen.add(line.strip())
                else:
                    offenders.append(f"{f.relative_to(ROOT)}:{n}")
    assert not offenders, offenders
    assert guard_seen == set(GUARD_LINES), (
        "the SKIP_OVERLAY_CHECK guard is missing or modified in "
        f"{GUARD_FILE.relative_to(ROOT)}"
    )
