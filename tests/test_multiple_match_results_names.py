"""Pin the per-endpoint ``multiple_match_results`` Literal names (issue #89).

Speakeasy's ``sharedErrorComponentsApr2025`` fix can hoist a per-endpoint
Literal to a top-level ``CodeMultipleMatchResults``. A regeneration that does
so silently renames shipped public models, so fail loudly here.
"""

import importlib
import typing

import pytest

CASES = (
    (
        "put_v2_lists_list_entriesop",
        "PutV2ListsListEntriesCodeMultipleMatchResults",
    ),
    (
        "put_v2_activities_activity_recordsop",
        "PutV2ActivitiesActivityRecordsCodeMultipleMatchResults",
    ),
)


@pytest.mark.parametrize(("module_name", "literal_name"), CASES)
def test_multiple_match_results_literal_name_is_stable(
    module_name: str, literal_name: str
) -> None:
    module = importlib.import_module(f"attio.models.{module_name}")
    models = importlib.import_module("attio.models")
    literal = getattr(module, literal_name)
    assert getattr(models, literal_name) is literal
    assert typing.get_args(literal) == ("multiple_match_results",)
    assert not hasattr(models, "CodeMultipleMatchResults")

