"""Pin the activity-record 401 ``code`` union names (issue #88).

Speakeasy can drop the response-class prefix on a ``code`` union that only
has 401 members (``ForbiddenCodeUnion`` -> ``CodeUnion``). A regeneration that
does so silently renames shipped public models, so fail loudly here.
"""

import importlib

import pytest

OPS = ("post", "put")


@pytest.mark.parametrize("verb", OPS)
@pytest.mark.parametrize("suffix", ("", "TypedDict"))
def test_forbidden_code_union_name_is_stable(verb: str, suffix: str) -> None:
    name = f"{verb.capitalize()}V2ActivitiesActivityRecordsForbiddenCodeUnion{suffix}"
    module = importlib.import_module(
        f"attio.models.{verb}_v2_activities_activity_recordsop"
    )
    assert hasattr(module, name)
    assert hasattr(importlib.import_module("attio.models"), name)
