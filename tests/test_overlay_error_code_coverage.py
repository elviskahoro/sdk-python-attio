"""End-to-end regression test for ``overlay.yaml`` error-code coverage.

An early draft of this PR (#81) proposed dropping the overlay action that
appends ``validation_type`` to the ``POST /v2/lists/{list}/entries`` 400
``code`` enum. The action was live against the pinned
``openapi/api-202610030405.json`` spec, so ``check-overlay`` would still
have reported 97 healthy targets and CI would still have turned green — but
the generated SDK ``PostV2ListsListEntriesBadRequestCode`` would have lost
``validation_type`` from its ``Literal[…]`` and any real response from the
Attio API returning ``"code": "validation_type"`` on that endpoint would
have raised ``ResponseValidationError`` at unmarshal time.

This test catches regressions of that shape in two ways:

1. **Action-present-but-ineffective:** every overlay action that intends
   ``validation_type`` to be accepted by a 400-error code union is parametrized
   against the generated ``*InvalidRequestErrorData`` Pydantic model, and a
   synthetic 400 response carrying ``code='validation_type'`` is round-tripped
   through ``TypeAdapter``. If the SDK rejects the code, the test fails with
   the endpoint and overlay target named.

2. **Action-removed-entirely:** ``EXPECTED_ENDPOINTS`` is a hand-fenced tuple of
   the (method, REST path) pairs that the overlay must cover. The set of
   endpoints the test parametrizes over is a *strict* subset of that fence
   (the fence asserts everything is included; parametrization runs only on
   the endpoints the overlay actually advertises). A removal that drops an
   action shrinks the parametrized set, and the matching assertion
   in ``test_overlay_yaml_fence_is_bidirectional`` fails loudly with
   the missing (method, path) quoted — so the regression surfaces in CI
   rather than shipping silently with a reduced-but-passing test count.

The companion ``check-overlay`` guard (``ci/spec_diff.py:_check_error_code_sync``)
covers the remaining direction: an overlay whose hardcoded ``replace:`` enum
drops a value the spec's ``anyOf`` union still carries. Together, these
three lenses — overlay-side enum coverage, generated-SDK Literal validation,
and the boundary fence — close the loop on regressions like the draft
removal above.
"""

from __future__ import annotations

import importlib
import json
import re
from pathlib import Path
from typing import Any

import pytest
import yaml
from pydantic import TypeAdapter, ValidationError

REPO_ROOT = Path(__file__).resolve().parent.parent
OVERLAY_YAML = REPO_ROOT / "overlay.yaml"

# Fenced coverage: every (method, REST path) endpoint that ``overlay.yaml``
# MUST advertise ``validation_type`` on, derived once from the pinned spec's
# 400 ``code`` schemas plus the cross-checked flatten pairs the overlay
# maintains. Update this tuple deliberately — a change means the
# overlay-side set of code-acceptance promises has changed, not just the
# discovery logic. Any removal that drops an action shrinks the overlay's
# coverage below this fence and is detected by
# ``test_overlay_yaml_fence_is_bidirectional``.
EXPECTED_ENDPOINTS: tuple[tuple[str, str], ...] = (
    ("patch", "/v2/{target}/{identifier}/attributes/{attribute}/options/{option}"),
    ("patch", "/v2/{target}/{identifier}/attributes/{attribute}/statuses/{status}"),
    ("post", "/v2/objects/{object}/records"),
    ("put", "/v2/objects/{object}/records"),
    # Activity-record write endpoints — flatten pairs added in #33.
    ("post", "/v2/activities/{activity}/records"),
    ("put", "/v2/activities/{activity}/records"),
    ("post", "/v2/objects/records/search"),
    ("post", "/v2/lists"),
    ("patch", "/v2/lists/{list}"),
    ("post", "/v2/lists/{list}/entries"),
    ("post", "/v2/comments"),
    ("post", "/v2/activities/{activity}/records"),
    ("put", "/v2/activities/{activity}/records"),
)

# Endpoints whose overlay.yaml action widens the 400 ``code`` field by adding
# ``validation_type``. Two shapes:
#   - ``code.enum append``: ``update: [validation_type]`` on a flat enum appends the value to
#     Speakeasy's merged output. The result is one Literal with both the
#     spec's values and ``validation_type``.
#   - ``anyOf flatten replace``: a paired ``remove: true`` on ``.code.anyOf`` and a full
#     ``update: {enum: [...]}`` on ``.code`` flattens a single-value-per-variant
#     anyOf into one Literal the SDK can type-check against.
# Both end up at the same downstream invariant this test pins: the SDK's
# 400-error code Literal must include ``validation_type``.
_VALIDATION_TYPE_TARGET_RE = re.compile(
    r"\$(?:\.paths)?(?:\[)?'?(?P<path>/v2/[^']+)'?\]?\."
    r"(?P<method>post|put|patch|delete|get)"
    r"\.responses\['400'\]"
)


def _overlay_endpoints() -> set[tuple[str, str]]:
    """Return the (method, REST path) set ``overlay.yaml`` actually advertises
    ``validation_type`` for. If the overlay format ever changes so that no
    action matches, this returns an empty set, and the fence in
    ``test_overlay_yaml_fence_is_bidirectional`` fails loudly."""
    with OVERLAY_YAML.open() as fh:
        doc = yaml.safe_load(fh) or {}
    found: set[tuple[str, str]] = set()
    for action in doc.get("actions") or []:
        target = action.get("target") or ""
        update = action.get("update")
        if "validation_type" not in str(update):
            continue
        m = _VALIDATION_TYPE_TARGET_RE.search(target)
        if not m:
            continue
        path = m.group("path")
        method = m.group("method")
        if isinstance(update, list):
            found.add((method, path))
        elif isinstance(update, dict):
            enum = update.get("enum") or []
            if isinstance(enum, list) and "validation_type" in enum:
                found.add((method, path))
    return found


def _errors_module_for(method: str, path: str) -> str:
    """Map (method, REST path) to the generated ``attio.errors.<module>`` name.

    The path's leading ``v2`` is part of the path itself; Speakeasy joins
    every segment with underscores and prefixes the result with the method
    (``<method_lower>_``). Trailing-segment rule: a placeholder final segment
    (e.g. ``/v2/.../{list}``) gives a ``_op`` suffix; a literal final
    segment (e.g. ``/v2/.../entries``) gives a no-underscore ``op`` suffix.
    """
    parts: list[str] = []
    for seg in path.strip("/").split("/"):
        parts.append(seg.strip("{}") if seg.startswith("{") else seg)
    trailing_is_placeholder = path.rstrip("/").rsplit("/", 1)[-1].startswith("{")
    suffix = "_op" if trailing_is_placeholder else "op"
    return f"attio.errors.{method.lower()}_" + "_".join(parts) + suffix


def _bad_request_class_name(method: str, path: str) -> str:
    """Map (method, REST path) to ``*InvalidRequestErrorData`` (the Pydantic class).

    Speakeasy's naming is ``<MethodTitle><PathSegmentsPascalCase><InvalidRequestErrorData>``:
    ``/v2/lists/{list}/entries`` POST → ``PostV2ListsListEntriesInvalidRequestErrorData``
    (``v2`` is part of the path and gets capitalized, ``{list}`` collapses to ``List``).
    """
    parts: list[str] = []
    for seg in path.strip("/").split("/"):
        cleaned = seg.strip("{}") if seg.startswith("{") else seg
        parts.append("".join(tok.capitalize() for tok in cleaned.split("_") if tok))
    return method.title() + "".join(parts) + "InvalidRequestErrorData"


SYNTHETIC_400 = {
    "status_code": 400,
    "type": "invalid_request_error",
    "code": "validation_type",
    "message": "Test message.",
}


def _import_class(module_name: str, class_name: str) -> Any:
    """Import a Pydantic class by dotted path; raise with both names on failure."""
    mod = importlib.import_module(module_name)
    try:
        return getattr(mod, class_name)
    except AttributeError as err:
        raise AttributeError(
            f"{module_name}.{class_name} not found — Speakeasy's generated "
            f"names changed; update the helpers in test_overlay_error_code_coverage.py"
        ) from err


# ---------------------------------------------------------------------------
# Fence: overlay.yaml must advertise at least the endpoints we promised.
# Catch silent action removal — if an action is deleted, the parametrized test
# count silently drops. This assertion fails loudly with the missing
# (method, path) quoted rather than passing with N-1 tests. The symmetric
# check (advertised ⊆ expected) catches the opposite drift: if a new
# endpoint is added to the overlay without being added to the fence, fail
# here so the maintainer sees it instead of shipping it uncovered.
# ---------------------------------------------------------------------------


def test_overlay_yaml_fence_is_bidirectional() -> None:
    advertised = _overlay_endpoints()
    expected = set(EXPECTED_ENDPOINTS)
    missing = expected - advertised
    unexpected = advertised - expected
    problems: list[str] = []
    if missing:
        problems.append(
            "overlay.yaml no longer advertises validation_type for at least "
            "one endpoint the suite expects covered. A future overlay would "
            "reject an API response containing `code='validation_type'` "
            "on the affected endpoint with no test failure to surface it:\n\n"
            + "\n".join(f"  - {method.upper()} {path}" for method, path in sorted(missing))
            + "\n\nIf an endpoint was deliberately retired, drop it from "
            "EXPECTED_ENDPOINTS in tests/test_overlay_error_code_coverage.py "
            "AND verify the new SDK shape (regenerate + check-post-merge)."
        )
    if unexpected:
        problems.append(
            "overlay.yaml advertises validation_type for at least one "
            "endpoint not in the fence. The SDK round-trip test parametrized "
            "from EXPECTED_ENDPOINTS would silently miss it. Either add the "
            "endpoint to EXPECTED_ENDPOINTS in "
            "tests/test_overlay_error_code_coverage.py or, if the new "
            "action is intentional and the endpoint isn't yet a real source "
            "of validation_type errors, drop the overlay action:\n\n"
            + "\n".join(f"  - {method.upper()} {path}" for method, path in sorted(unexpected))
        )
    if problems:
        pytest.fail("\n\n---\n\n".join(problems))


# ---------------------------------------------------------------------------
# SDK-side acceptance: every endpoint currently advertised by overlay.yaml
# as accepting ``validation_type`` must round-trip a synthetic 400 response
# through its generated ``InvalidRequestErrorData`` Pydantic model.
# ---------------------------------------------------------------------------


def _parametrize_overlap() -> list[dict[str, Any]]:
    """Build the per-test endpoint dicts, restricted to the fence.

    Restricting to ``expected ∩ advertised`` ensures each generated test has
    both a contract (the fence) and a current action (overlay.yaml). If an
    expected endpoint is also advertised, parametrize over it; if the fence
    is larger than the overlay (overlay missing an action), the Fence test
    above fails, and these tests stop running on the missing endpoint — which
    is the right surface for a missing-action regression.
    """
    advertised = _overlay_endpoints()
    expected = set(EXPECTED_ENDPOINTS)
    out: list[dict[str, Any]] = []
    for method, path in sorted(expected & advertised):
        out.append(
            {
                "method": method,
                "path": path,
            }
        )
    return out


@pytest.mark.parametrize(
    "endpoint",
    _parametrize_overlap(),
    ids=lambda ep: f"{ep['method'].upper()} {ep['path']}",
)
def test_sdk_accepts_validation_type(endpoint: dict[str, Any]) -> None:
    """The endpoint advertised by overlay.yaml as accepting ``validation_type``
    must round-trip a synthetic 400 response through its generated
    ``InvalidRequestErrorData`` Pydantic model. The draft removal above would
    have regressed here too: dropping the overlay action also walks the
    generated Literal down to ``[value_not_found]``."""
    module_name = _errors_module_for(endpoint["method"], endpoint["path"])
    class_name = _bad_request_class_name(endpoint["method"], endpoint["path"])
    model = _import_class(module_name, class_name)
    adapter = TypeAdapter(model)
    try:
        adapter.validate_python(SYNTHETIC_400)
    except ValidationError as err:
        errors = err.errors()
        # Only flag code-rejection errors. Other shape issues (e.g. type
        # schema drift) are noise here — they're covered elsewhere.
        offending = [e for e in errors if "code" in (e.get("loc") or ())]
        if offending:
            pytest.fail(
                f"{endpoint['method'].upper()} {endpoint['path']}: "
                f"generated SDK rejects `code='validation_type'` on a 400 response "
                f"— overlay.yaml promises it but the SDK Literal does not include it. "
                f"Pydantic errors: {json.dumps(offending, default=str, indent=2)}"
            )
        # Code is fine; some other field rejected. Surface for awareness.
        pytest.fail(
            f"{endpoint['method'].upper()} {endpoint['path']}: 400 round-trip "
            f"failed for a non-code reason — update SYNTHETIC_400 if the "
            f"InvalidRequestErrorData schema has legitimately changed.\n"
            f"{json.dumps(errors, default=str, indent=2)}"
        )
