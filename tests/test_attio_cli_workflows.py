from __future__ import annotations

import json
from types import SimpleNamespace as NS

import pytest

from attio_cli import main as cli_main
from attio_cli.people import CLIError
from attio_cli.query import (
    CompanyPayload,
    NoteAddPayload,
    NoteListPayload,
    NoteUpdatePayload,
    PersonUpsertQuery,
)
from attio_cli.workflows import (
    add_company,
    add_note,
    add_person,
    list_notes,
    search_companies,
    search_people,
    update_company,
    update_note,
    update_person,
)


def _record(record_id: str, *, email: str | None = None, name: str | None = None):
    values = {"email_addresses": [NS(email_address=email)] if email else []}
    if name:
        values["name"] = [NS(first_name=name, last_name="", full_name=name)]
    return NS(id=NS(record_id=record_id), values=values)


class _Records:
    def __init__(self, matches=None, existing=None, written=None):
        self.matches = matches or []
        self.existing = existing or _record("existing")
        self.written = written or _record("written")
        self.calls = []

    def post_v2_objects_object_records_query(self, **kwargs):
        self.calls.append(("query", kwargs))
        return NS(data=self.matches)

    def get_v2_objects_object_records_record_id_(self, **kwargs):
        self.calls.append(("get", kwargs))
        return NS(data=self.existing)

    def post_v2_objects_object_records(self, **kwargs):
        self.calls.append(("post", kwargs))
        return NS(data=self.written)

    def patch_v2_objects_object_records_record_id_(self, **kwargs):
        self.calls.append(("patch", kwargs))
        return NS(data=self.written)

    def put_v2_objects_object_records_record_id_(self, **kwargs):
        self.calls.append(("put", kwargs))
        return NS(data=self.written)


class _Notes:
    def __init__(self):
        self.calls = []
        self.note = NS(id=NS(note_id="note-1"), title="Call", content_plaintext="Details")

    def get_v2_notes(self, **kwargs):
        self.calls.append(("list", kwargs))
        return NS(data=[self.note])

    def post_v2_notes(self, **kwargs):
        self.calls.append(("add", kwargs))
        return NS(data=self.note)

    def patch_v2_notes_note_id_(self, **kwargs):
        self.calls.append(("update", kwargs))
        return NS(data=self.note)


class _Client:
    def __init__(self, records=None, notes=None):
        self.records = records or _Records()
        self.notes = notes or _Notes()


def test_people_search_is_exact_and_returns_versioned_results():
    records = _Records(matches=[_record("person-1", email="ada@example.com")])
    result = search_people(" Ada@Example.com ", _Client(records=records))

    assert records.calls[0][1]["filter_"] == {"email_addresses": "ada@example.com"}
    assert result["action"] == "searched"
    assert result["meta"]["output_schema_version"] == "v1"
    assert result["meta"]["results"][0]["id"]["record_id"] == "person-1"


def test_people_add_rejects_existing_identity_before_writing():
    records = _Records(matches=[_record("person-1", email="ada@example.com")])
    with pytest.raises(CLIError, match="already matches") as exc_info:
        add_person(PersonUpsertQuery(email="ada@example.com"), _Client(records=records))
    assert exc_info.value.code == "duplicate_identity"
    assert [method for method, _ in records.calls] == ["query"]


def test_people_add_and_update_write_expected_partial_values():
    new_records = _Records(written=_record("person-new", email="ada@example.com"))
    created = add_person(
        PersonUpsertQuery(email="ada@example.com", first_name="Ada"),
        _Client(records=new_records),
    )
    assert created["action"] == "created"
    post = next(kwargs for method, kwargs in new_records.calls if method == "post")
    assert post["data"]["values"]["name"][0]["first_name"] == "Ada"

    existing = _record("person-1", email="ada@example.com", name="Ada")
    records = _Records(
        matches=[existing], existing=existing,
        written=_record("person-1", email="ada@example.com", name="Augusta"),
    )
    updated = update_person(
        PersonUpsertQuery(email="ada@example.com", first_name="Augusta"),
        _Client(records=records),
    )
    patch = next(kwargs for method, kwargs in records.calls if method == "patch")
    assert updated["action"] == "updated"
    assert patch["record_id"] == "person-1"
    assert patch["data"]["values"]["name"][0]["full_name"] == "Augusta"


def test_people_update_rejects_missing_and_ambiguous_matches():
    with pytest.raises(CLIError, match="No person matches"):
        update_person(
            PersonUpsertQuery(email="missing@example.com", job_title="Engineer"), _Client()
        )

    records = _Records(matches=[_record("a"), _record("b")])
    with pytest.raises(CLIError, match="update was not applied"):
        update_person(
            PersonUpsertQuery(email="ada@example.com", job_title="Engineer"),
            _Client(records=records),
        )
    assert [method for method, _ in records.calls] == ["query"]


def test_company_commands_use_normalized_domain_and_reject_duplicates():
    records = _Records(written=_record("company-1"))
    payload = CompanyPayload(domain="Example.com", values={"name": [{"value": "Example"}]})
    created = add_company(payload, _Client(records=records))
    query = next(kwargs for method, kwargs in records.calls if method == "query")
    post = next(kwargs for method, kwargs in records.calls if method == "post")
    assert query["object"] == "companies"
    assert query["filter_"] == {"domains": "example.com"}
    assert post["data"]["values"]["domains"] == [{"domain": "example.com"}]
    assert created["record_id"] == "company-1"

    duplicate = _Records(matches=[_record("company-1")])
    with pytest.raises(CLIError, match="already matches domain"):
        add_company(CompanyPayload(domain="example.com"), _Client(records=duplicate))
    assert [method for method, _ in duplicate.calls] == ["query"]


def test_company_update_requires_one_match_and_preserves_partial_payload():
    existing = _record("company-1")
    records = _Records(matches=[existing], written=existing)
    result = update_company(
        CompanyPayload(domain="example.com", values={"description": ["Updated"]}),
        _Client(records=records),
    )
    patch = next(kwargs for method, kwargs in records.calls if method == "patch")
    assert result["action"] == "updated"
    assert patch["record_id"] == "company-1"
    assert patch["data"]["values"] == {
        "description": ["Updated"], "domains": [{"domain": "example.com"}]
    }

    records = _Records(matches=[_record("a"), _record("b")])
    with pytest.raises(CLIError, match="update was not applied"):
        update_company(
            CompanyPayload(domain="example.com", values={"description": ["x"]}),
            _Client(records=records),
        )
    assert [method for method, _ in records.calls] == ["query"]


def test_note_list_add_and_update_use_supported_sdk_shapes():
    notes = _Notes()
    client = _Client(notes=notes)
    listed = list_notes(
        NoteListPayload(parent_object="people", parent_record_id="person-1"), client
    )
    assert listed["action"] == "listed"
    assert listed["meta"]["results"][0]["id"]["note_id"] == "note-1"

    added = add_note(
        NoteAddPayload(
            parent_object="people", parent_record_id="person-1", title="Call",
            content="Details", format="markdown",
        ),
        client,
    )
    create_data = notes.calls[1][1]["data"]
    assert create_data["format_"] == "markdown"
    assert added["record_id"] == "note-1"

    updated = update_note(
        NoteUpdatePayload(note_id="note-1", content="New content"), client
    )
    assert notes.calls[2][1]["data"] == {"content": "New content"}
    assert updated["action"] == "updated"


def test_note_input_models_reject_empty_updates_and_invalid_pages():
    with pytest.raises(ValueError):
        NoteUpdatePayload(note_id="note-1")
    with pytest.raises(ValueError):
        NoteListPayload(parent_object="people", parent_record_id="person-1", limit=0)
    with pytest.raises(ValueError, match="reserved"):
        CompanyPayload(
            domain="example.com", values={"domains": [{"domain": "other.com"}]}
        )


def test_new_command_json_validation_and_help(monkeypatch, capsys):
    monkeypatch.setattr(cli_main, "_load_credentials", lambda: "test-key")
    status = cli_main.main(["companies", "add", "--json", "not-json"])
    output = json.loads(capsys.readouterr().out)
    assert status == 1
    assert output["errors"][0]["code"] == "invalid_json"

    with pytest.raises(SystemExit) as exc_info:
        cli_main.main(["notes", "--help"])
    assert exc_info.value.code == 0
    assert "list" in capsys.readouterr().out


def test_company_search_returns_structured_results():
    records = _Records(matches=[_record("company-1")])
    result = search_companies(CompanyPayload(domain="example.com"), _Client(records=records))
    assert result["action"] == "searched"
    assert result["meta"]["identity"] == {"domain": "example.com"}
    assert result["meta"]["results"][0]["id"]["record_id"] == "company-1"


def test_people_search_warns_when_result_limit_is_reached():
    records = _Records(matches=[_record(f"person-{index}") for index in range(50)])
    result = search_people("ada@example.com", _Client(records=records))
    assert result["partial_success"] is True
    assert result["warnings"][0]["code"] == "search_result_limit_reached"


def test_add_person_maps_create_race_to_duplicate_identity():
    records = _Records()

    def conflict(**kwargs):
        raise RuntimeError(
            '{"code":"uniqueness_conflict","message":"Email already exists"}'
        )

    records.post_v2_objects_object_records = conflict
    with pytest.raises(CLIError, match="ada@example.com") as exc_info:
        add_person(PersonUpsertQuery(email="ada@example.com"), _Client(records=records))
    assert exc_info.value.code == "duplicate_identity"


def test_update_person_preserves_email_case_for_merges_and_replacement():
    existing = _record("person-1", email="Ada@Example.com")
    query = PersonUpsertQuery(
        email=" ADA@EXAMPLE.COM ", additional_emails=["Work@Example.com"]
    )

    merge_records = _Records(matches=[existing], existing=existing, written=existing)
    update_person(query, _Client(records=merge_records))
    patch = next(kwargs for method, kwargs in merge_records.calls if method == "patch")
    assert patch["data"]["values"]["email_addresses"] == [
        {"email_address": "Ada@Example.com"},
        {"email_address": "Work@Example.com"},
    ]

    replace_records = _Records(matches=[existing], existing=existing, written=existing)
    update_person(
        query.model_copy(update={"replace_emails": True}),
        _Client(records=replace_records),
    )
    put = next(kwargs for method, kwargs in replace_records.calls if method == "put")
    assert put["data"]["values"]["email_addresses"] == [
        {"email_address": "ADA@EXAMPLE.COM"},
        {"email_address": "Work@Example.com"},
    ]

    add_records = _Records(written=_record("person-new", email="Ada@Example.com"))
    add_person(
        PersonUpsertQuery(email="Ada@Example.com"), _Client(records=add_records)
    )
    create = next(kwargs for method, kwargs in add_records.calls if method == "post")
    assert create["data"]["values"]["email_addresses"] == [
        {"email_address": "Ada@Example.com"}
    ]


@pytest.mark.parametrize(
    "query",
    [
        PersonUpsertQuery(email="ada@example.com", notes=""),
        PersonUpsertQuery(email="ada@example.com", linkedin="not a profile"),
    ],
)
def test_update_person_rejects_empty_effective_values_without_writing(query):
    records = _Records(matches=[_record("person-1")])
    with pytest.raises(CLIError, match="No valid person fields"):
        update_person(query, _Client(records=records))
    assert not any(method in {"patch", "put"} for method, _ in records.calls)


def test_company_add_maps_uniqueness_race_to_duplicate_identity():
    records = _Records()

    def conflict(**kwargs):
        raise RuntimeError('{"code":"uniqueness_conflict"}')

    records.post_v2_objects_object_records = conflict
    with pytest.raises(CLIError, match="example.com") as exc_info:
        add_company(CompanyPayload(domain="example.com"), _Client(records=records))
    assert exc_info.value.code == "duplicate_identity"


def test_people_search_add_and_update_dispatch_through_main(monkeypatch, capsys):
    monkeypatch.setattr(cli_main, "_load_credentials", lambda: "test-key")
    person = _record("person-1", email="ada@example.com", name="Ada")
    scenarios = [
        (["people", "search", "ada@example.com"], _Records(matches=[person])),
        (["people", "add", "new@example.com", "--first-name", "Ada"], _Records()),
        (
            ["people", "update", "ada@example.com", "--job-title", "Engineer"],
            _Records(matches=[person], existing=person, written=person),
        ),
    ]

    for argv, records in scenarios:
        client = _Client(records=records)

        class _SDK:
            def __init__(self, *, oauth2):
                assert oauth2 == "test-key"

            def __enter__(self):
                return client

            def __exit__(self, *_exc):
                return None

        monkeypatch.setattr(cli_main, "SDK", _SDK)
        assert cli_main.main(argv) == 0
        result = json.loads(capsys.readouterr().out)
        assert result["success"] is True
        assert records.calls[0][0] == "query"


def test_people_add_rejects_unused_replace_emails_option(capsys):
    with pytest.raises(SystemExit) as exc_info:
        cli_main.main(["people", "add", "ada@example.com", "--replace-emails"])
    assert exc_info.value.code == 2
    assert "--replace-emails" in capsys.readouterr().err


def test_cli_wraps_api_errors_for_new_commands(monkeypatch, capsys):
    class _BrokenRecords(_Records):
        def post_v2_objects_object_records_query(self, **kwargs):
            raise RuntimeError('{"status_code":503,"code":"service_unavailable"}')

    class _SDK:
        def __init__(self, *, oauth2):
            assert oauth2 == "test-key"

        def __enter__(self):
            return _Client(records=_BrokenRecords())

        def __exit__(self, *_exc):
            return None

    monkeypatch.setattr(cli_main, "_load_credentials", lambda: "test-key")
    monkeypatch.setattr(cli_main, "SDK", _SDK)

    status = cli_main.main(
        ["companies", "search", "--json", '{"domain":"example.com"}']
    )
    result = json.loads(capsys.readouterr().out)
    assert status == 1
    assert result["action"] == "failed"
    assert result["errors"][0]["code"] == "service_unavailable"
