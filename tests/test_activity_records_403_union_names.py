"""Pin the activity-record 403 ``code`` model names (issue #88).

Attio's spec now lists a single ``unauthorized`` code for the 403 response
(``billing_error`` was dropped), so there is no 403 union any more: the code is
a plain literal. Fail loudly if a regeneration renames it.
"""

import importlib

import pytest

OPS = ("post", "put")


@pytest.mark.parametrize("verb", OPS)
def test_forbidden_code_literal_name_is_stable(verb: str) -> None:
    name = f"{verb.capitalize()}V2ActivitiesActivityRecordsCodeUnauthorized"
    module = importlib.import_module(
        f"attio.models.{verb}_v2_activities_activity_recordsop"
    )
    assert hasattr(module, name)
    assert hasattr(importlib.import_module("attio.models"), name)
