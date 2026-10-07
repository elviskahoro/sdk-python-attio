from __future__ import annotations

import json
import os
from types import SimpleNamespace as NS

import httpx
import pytest
from pydantic import ValidationError

from attio.errors.patch_v2_objects_object_records_record_id_op import (
    PatchV2ObjectsObjectRecordsRecordIDNotFoundError,
    PatchV2ObjectsObjectRecordsRecordIDNotFoundErrorData,
)
from attio_cli import main as cli_main
import attio_cli.people as people_cli
from attio_cli.people import (
    CLIError,
    _build_core_values,
    _build_optional_values,
    _detect_optional_field,
    _format_linkedin,
    _write_with_optional_fallback,
    error_envelope,
    execute_upsert,
    normalize_emails,
    upsert_person,
)
from attio_cli.query import PersonUpsertQuery
from _attio_cli_helpers import FakeClient as _FakeClient
from _attio_cli_helpers import FakeRecords as _FakeRecords
from _attio_cli_helpers import record as _record


def _attribute_not_found(field: str, *, wording: str = "standard") -> RuntimeError:
    if wording == "cannot_find":
        message = f'Cannot find attribute with slug/ID "{field}".'
    else:
        message = f'Attribute with slug/ID "{field}" not found.'
    return RuntimeError(
        json.dumps(
            {
                "status_code": 404,
                "type": "invalid_request_error",
                "code": "not_found",
                "message": message,
            }
        )
    )


def test_normalize_emails_strips_and_deduplicates_case_insensitively():
    assert normalize_emails([" Ada@example.com ", "ada@example.com", None, " "]) == [
        "Ada@example.com"
    ]


def test_core_values_map_email_name_phone_and_linkedin():
    query = PersonUpsertQuery(
        email="ada@example.com",
        first_name="Ada",
        last_name="Lovelace",
        job_title="Mathematician",
        phone="+44 20 1234 5678",
        linkedin="ada-lovelace",
    )
    assert _build_core_values(query) == {
        "email_addresses": [{"email_address": "ada@example.com"}],
        "name": [{
            "first_name": "Ada",
            "last_name": "Lovelace",
            "full_name": "Ada Lovelace",
        }],
        "job_title": ["Mathematician"],
        "phone_numbers": [{"original_phone_number": "+44 20 1234 5678"}],
        "linkedin": ["https://www.linkedin.com/in/ada-lovelace"],
    }


def test_international_phone_numbers_do_not_assume_a_country():
    international = PersonUpsertQuery(email="ada@example.com", phone="+49 30 123456")
    assert _build_core_values(international)["phone_numbers"] == [
        {"original_phone_number": "+49 30 123456"}
    ]

    local = PersonUpsertQuery(
        email="ada@example.com", phone="555-1234", phone_country_code="GB"
    )
    assert _build_core_values(local)["phone_numbers"] == [
        {"original_phone_number": "555-1234", "country_code": "GB"}
    ]
    assert "phone_numbers" not in _build_core_values(
        PersonUpsertQuery(email="ada@example.com", phone="555-1234")
    )


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("https://www.linkedin.com/in/x/", ["https://www.linkedin.com/in/x"]),
        ("linkedin.com/in/x/", None),
    ],
)
def test_linkedin_profile_url_edge_cases(value, expected):
    assert _format_linkedin(value) == expected


def test_location_contains_all_composite_siblings_and_requires_country():
    query = PersonUpsertQuery(
        email="ada@example.com",
        location="London, England",
        country_code="GB",
    )
    location = _build_optional_values(query)["primary_location"][0]
    assert location == {
        "line_1": None,
        "line_2": None,
        "line_3": None,
        "line_4": None,
        "locality": "London",
        "region": "England",
        "postcode": None,
        "country_code": "GB",
        "latitude": None,
        "longitude": None,
    }
    with pytest.raises(ValidationError, match="country-code is required"):
        PersonUpsertQuery(email="ada@example.com", location="London")
    with pytest.raises(ValidationError, match="two-letter ISO-3166-1"):
        PersonUpsertQuery(email="ada@example.com", country_code="USA")


def test_raw_location_mode_maps_street_locality_and_region():
    query = PersonUpsertQuery(
        email="ada@example.com",
        location="10 Downing Street, London, England",
        country_code="GB",
        location_mode="raw",
    )
    location = _build_optional_values(query)["primary_location"][0]
    assert location["line_1"] == "10 Downing Street"
    assert location["locality"] == "London"
    assert location["region"] == "England"


@pytest.mark.parametrize(
    ("value", "line_1", "locality", "region"),
    [
        ("London", "London", None, None),
        ("10 Downing Street, London", "10 Downing Street", "London", None),
    ],
)
def test_raw_location_mode_accepts_short_values(value, line_1, locality, region):
    query = PersonUpsertQuery(
        email="ada@example.com",
        location=value,
        country_code="GB",
        location_mode="raw",
    )
    location = _build_optional_values(query)["primary_location"][0]
    assert (location["line_1"], location["locality"], location["region"]) == (
        line_1,
        locality,
        region,
    )


def test_create_when_no_email_match():
    records = _FakeRecords(
        written=_record("new-id", ["ada@example.com"], "Ada Lovelace")
    )
    result = upsert_person(PersonUpsertQuery(email="ada@example.com"), _FakeClient(records))
    assert [call[0] for call in records.calls] == ["query", "post"]
    assert result["action"] == "created"
    assert result["record_id"] == "new-id"
    assert result["meta"]["person"]["created"] is True


def test_create_race_reports_uniqueness_conflict():
    records = _FakeRecords()

    def conflict(**kwargs):
        raise RuntimeError('{"code":"uniqueness_conflict"}')

    records.post_v2_objects_object_records = conflict
    with pytest.raises(CLIError, match="ada@example.com") as exc_info:
        upsert_person(
            PersonUpsertQuery(email="ada@example.com"), _FakeClient(records)
        )
    assert exc_info.value.code == "uniqueness_conflict"


def test_create_race_names_conflicting_additional_email():
    records = _FakeRecords()

    def conflict(**kwargs):
        raise RuntimeError(
            '{"code":"uniqueness_conflict",'
            '"message":"Email new@example.com already exists."}'
        )

    records.post_v2_objects_object_records = conflict
    with pytest.raises(CLIError, match="new@example.com"):
        upsert_person(
            PersonUpsertQuery(
                email="ada@example.com", additional_emails=["new@example.com"]
            ),
            _FakeClient(records),
        )


def test_upsert_strips_email_before_search_and_write():
    records = _FakeRecords(written=_record("new-id", ["ada@example.com"]))
    upsert_person(PersonUpsertQuery(email="  ada@example.com  "), _FakeClient(records))
    query = next(kwargs for method, kwargs in records.calls if method == "query")
    create = next(kwargs for method, kwargs in records.calls if method == "post")
    assert query["filter_"] == {"email_addresses": "ada@example.com"}
    assert create["data"]["values"]["email_addresses"] == [
        {"email_address": "ada@example.com"}
    ]


def test_execute_upsert_configures_generated_sdk_oauth_client(monkeypatch):
    client = object()
    initialized = {}

    class FakeSDK:
        def __init__(self, *, oauth2):
            initialized["oauth2"] = oauth2

        def __enter__(self):
            return client

        def __exit__(self, *_exc):
            initialized["closed"] = True

    monkeypatch.setattr(people_cli, "SDK", FakeSDK)
    monkeypatch.setattr(people_cli, "upsert_person", lambda query, sdk: (query, sdk))
    query = PersonUpsertQuery(email="ada@example.com")

    assert execute_upsert("secret-key", query) == (query, client)
    assert initialized == {"oauth2": "secret-key", "closed": True}


def test_update_one_match_merges_and_deduplicates_emails():
    records = _FakeRecords(
        matches=[_record("existing")],
        existing=_record("existing", ["ada@example.com", "ada@old.example"]),
        written=_record("existing", ["ada@example.com", "ada@old.example", "ada@work.example"]),
    )
    result = upsert_person(
        PersonUpsertQuery(
            email="ada@example.com",
            additional_emails=["ADA@OLD.EXAMPLE", "ada@work.example"],
        ),
        _FakeClient(records),
    )
    put = next(kwargs for method, kwargs in records.calls if method == "put")
    assert put["data"]["values"]["email_addresses"] == [
        {"email_address": "ada@example.com"},
        {"email_address": "ada@old.example"},
        {"email_address": "ada@work.example"},
    ]
    assert [w["code"] for w in result["warnings"]] == ["multiple_emails_added"]
    assert result["meta"]["person"]["email_addresses"][-1] == "ada@work.example"


def test_partial_name_update_preserves_existing_name_component():
    existing = _record("existing", ["ada@example.com"])
    existing.values["name"] = [
        NS(first_name="Ada", last_name="Lovelace", full_name="Ada Lovelace")
    ]
    records = _FakeRecords(
        matches=[_record("existing")],
        existing=existing,
        written=_record("existing", ["ada@example.com"], "Augusta Lovelace"),
    )

    upsert_person(
        PersonUpsertQuery(email="ada@example.com", first_name="Augusta"),
        _FakeClient(records),
    )

    put = next(kwargs for method, kwargs in records.calls if method == "put")
    assert put["data"]["values"]["name"] == [
        {
            "first_name": "Augusta",
            "last_name": "Lovelace",
            "full_name": "Augusta Lovelace",
        }
    ]


def test_replace_emails_replaces_existing_addresses():
    records = _FakeRecords(
        matches=[_record("existing")],
        existing=_record("existing", ["old@example.com"]),
        written=_record("existing", ["ada@example.com", "new@example.com"]),
    )
    upsert_person(
        PersonUpsertQuery(
            email="ada@example.com",
            additional_emails=["new@example.com"],
            replace_emails=True,
        ),
        _FakeClient(records),
    )
    put = next(kwargs for method, kwargs in records.calls if method == "put")
    assert put["data"]["values"]["email_addresses"] == [
        {"email_address": "ada@example.com"},
        {"email_address": "new@example.com"},
    ]


def test_update_email_uniqueness_conflict_names_requested_address():
    records = _FakeRecords(
        matches=[_record("existing")],
        existing=_record("existing", ["ada@example.com"]),
    )

    def conflict(**kwargs):
        raise RuntimeError(
            '{"status_code":400,"type":"invalid_request_error",'
            '"code":"uniqueness_conflict","message":"Email already in use."}'
        )

    records.put_v2_objects_object_records_record_id_ = conflict
    with pytest.raises(CLIError, match="new@example.com") as exc_info:
        upsert_person(
            PersonUpsertQuery(
                email="ada@example.com", additional_emails=["new@example.com"]
            ),
            _FakeClient(records),
        )
    assert exc_info.value.code == "uniqueness_conflict"


def test_multiple_matches_pick_lowest_id_and_emit_warning():
    records = _FakeRecords(
        matches=[_record("z-record"), _record("a-record")],
        existing=_record("a-record", ["ada@example.com"]),
        written=_record("a-record", ["ada@example.com"]),
    )
    result = upsert_person(
        PersonUpsertQuery(email="ada@example.com"), _FakeClient(records)
    )
    assert result["record_id"] == "a-record"
    assert result["partial_success"] is True
    assert result["warnings"][0]["code"] == "upsert_multi_match_selected_record"
    get_call = next(kwargs for method, kwargs in records.calls if method == "get")
    assert get_call["record_id"] == "a-record"


def test_search_limit_is_reported_when_duplicate_page_is_full():
    records = _FakeRecords(
        matches=[_record(f"record-{index:02d}") for index in range(50)],
        existing=_record("record-00", ["ada@example.com"]),
        written=_record("record-00", ["ada@example.com"]),
    )
    result = upsert_person(
        PersonUpsertQuery(email="ada@example.com"), _FakeClient(records)
    )
    query = next(kwargs for method, kwargs in records.calls if method == "query")
    get_call = next(kwargs for method, kwargs in records.calls if method == "get")
    assert query["limit"] == 50
    assert get_call["record_id"] == "record-00"
    assert result["partial_success"] is True
    assert "upsert_multi_match_result_limit_reached" in {
        warning["code"] for warning in result["warnings"]
    }


def test_multiple_matches_strict_mode_fails_without_writing():
    records = _FakeRecords(matches=[_record("a"), _record("b")])
    with pytest.raises(CLIError, match="strict mode rejects ambiguity"):
        upsert_person(
            PersonUpsertQuery(email="ada@example.com", strict=True),
            _FakeClient(records),
        )
    assert [method for method, _ in records.calls] == ["query"]


def test_optional_field_fallback_warns_or_fails_strictly():
    calls = []

    def write(values):
        calls.append(values)
        if "notes" in values:
            raise _attribute_not_found("notes")
        return "ok"

    response, warnings, skipped = _write_with_optional_fallback(
        write,
        {"email_addresses": []},
        {"notes": ["hello"]},
        strict=False,
    )
    assert response == "ok"
    assert len(calls) == 2
    assert warnings[0]["code"] == "attio_notes_field_unavailable"
    assert skipped == [{"field": "notes", "reason": "schema_mismatch"}]

    with pytest.raises(CLIError, match="Optional field unavailable"):
        _write_with_optional_fallback(
            write, {}, {"notes": ["hello"]}, strict=True
        )


def test_optional_field_fallback_accepts_attio_not_found_wordings():
    assert _detect_optional_field(_attribute_not_found("notes")) == "notes"
    assert (
        _detect_optional_field(
            _attribute_not_found("notes", wording="cannot_find")
        )
        == "notes"
    )


def test_optional_field_detection_uses_generated_sdk_error_shape():
    payload = {
        "status_code": 404,
        "type": "invalid_request_error",
        "code": "not_found",
        "message": 'Attribute with slug/ID "notes" not found.',
    }
    body = json.dumps(payload)
    sdk_error = PatchV2ObjectsObjectRecordsRecordIDNotFoundError(
        PatchV2ObjectsObjectRecordsRecordIDNotFoundErrorData.model_validate(payload),
        httpx.Response(404, text=body),
        body,
    )
    assert _detect_optional_field(sdk_error) == "notes"
    envelope = error_envelope(sdk_error)
    assert envelope["errors"][0]["status_code"] == 404
    assert envelope["errors"][0]["code"] == "not_found"


def test_company_attribute_alias_is_tried_before_skipping():
    calls = []

    def write(values):
        calls.append(values)
        if "associated_company" in values:
            raise _attribute_not_found("associated_company")
        return values

    response, warnings, skipped = _write_with_optional_fallback(
        write,
        {},
        {"associated_company": [{"target_object": "companies"}]},
        strict=False,
    )
    assert "company" in response
    assert len(calls) == 2
    assert warnings == []
    assert skipped == []


def test_unrelated_error_mentioning_optional_field_is_not_schema_fallback():
    def write(values):
        raise RuntimeError(
            '{"status_code":400,"type":"invalid_request_error",'
            '"code":"validation_type","message":"Invalid notes value."}'
        )

    with pytest.raises(RuntimeError, match="Invalid notes value"):
        _write_with_optional_fallback(write, {}, {"notes": ["bad"]}, strict=False)


def test_optional_field_fallback_is_used_during_record_update():
    records = _FakeRecords(
        matches=[_record("existing")],
        existing=_record("existing", ["ada@example.com"]),
    )

    def put(**kwargs):
        records.calls.append(("put", kwargs))
        if "notes" in kwargs["data"]["values"]:
            raise _attribute_not_found("notes")
        return NS(data=records.written)

    records.put_v2_objects_object_records_record_id_ = put
    result = upsert_person(
        PersonUpsertQuery(email="ada@example.com", notes="hello"),
        _FakeClient(records),
    )
    assert len([call for call in records.calls if call[0] == "put"]) == 2
    assert result["warnings"][0]["code"] == "attio_notes_field_unavailable"
    assert result["skipped_fields"] == [
        {"field": "notes", "reason": "schema_mismatch"}
    ]


def test_invalid_optional_values_warn_and_strict_mode_fails():
    query = PersonUpsertQuery(
        email="ada@example.com",
        linkedin="https://example.com/not-linkedin",
        company_domain="not a domain",
        country_code="US",
    )
    records = _FakeRecords(written=_record("new-id", ["ada@example.com"]))
    result = upsert_person(query, _FakeClient(records))
    assert result["partial_success"] is True
    assert {warning["field"] for warning in result["warnings"]} == {
        "linkedin",
        "company_domain",
        "country_code",
    }
    assert {item["reason"] for item in result["skipped_fields"]} == {"invalid_value"}

    strict_records = _FakeRecords()
    with pytest.raises(CLIError, match="LinkedIn value"):
        upsert_person(
            query.model_copy(update={"strict": True}), _FakeClient(strict_records)
        )
    assert strict_records.calls == []


def test_local_phone_requires_explicit_country_and_strict_rejects_omission():
    query = PersonUpsertQuery(email="ada@example.com", phone="20 1234 5678")
    records = _FakeRecords(written=_record("new-id", ["ada@example.com"]))
    result = upsert_person(query, _FakeClient(records))
    assert result["partial_success"] is True
    assert result["warnings"][0]["field"] == "phone"
    assert result["skipped_fields"] == [{"field": "phone", "reason": "invalid_value"}]
    create = next(kwargs for method, kwargs in records.calls if method == "post")
    assert "phone_numbers" not in create["data"]["values"]

    with pytest.raises(CLIError, match="requires --phone-country-code"):
        upsert_person(
            query.model_copy(update={"strict": True}), _FakeClient(_FakeRecords())
        )


def test_cli_json_input_overrides_flags_and_always_emits_envelope(monkeypatch, capsys):
    captured = {}
    monkeypatch.setattr(cli_main, "_load_credentials", lambda: "test-key")

    def execute(api_key, query):
        captured["api_key"] = api_key
        captured["query"] = query
        return {
            "success": True,
            "partial_success": False,
            "action": "created",
            "record_id": "record-1",
            "warnings": [],
            "skipped_fields": [],
            "errors": [],
            "meta": {"output_schema_version": "v1"},
        }

    monkeypatch.setattr(cli_main, "execute_upsert", execute)
    status = cli_main.main(
        [
            "people",
            "upsert",
            "ignored@example.com",
            "--first-name",
            "Ignored",
            "--json",
            '{"email":"ada@example.com","first_name":"Ada","phone_country_code":"GB"}',
        ]
    )
    output = capsys.readouterr().out
    assert status == 0
    assert captured["api_key"] == "test-key"
    assert captured["query"].email == "ada@example.com"
    assert captured["query"].first_name == "Ada"
    assert captured["query"].phone_country_code == "GB"
    assert json.loads(output)["action"] == "created"


def test_invalid_json_input_is_structured_failure(monkeypatch, capsys):
    status = cli_main.main(["people", "upsert", "--json", "not-json"])
    result = json.loads(capsys.readouterr().out)
    assert status == 1
    assert result["action"] == "failed"
    assert result["errors"][0]["code"] == "invalid_json"


def test_unknown_json_fields_fail_validation(monkeypatch, capsys):
    status = cli_main.main(
        ["people", "upsert", "--json", '{"email":"ada@example.com","typo":"x"}']
    )
    result = json.loads(capsys.readouterr().out)
    assert status == 1
    assert result["errors"][0]["code"] == "validation_error"


def test_json_array_is_rejected_as_non_object(capsys):
    status = cli_main.main(["people", "upsert", "--json", "[]"])
    result = json.loads(capsys.readouterr().out)
    assert status == 1
    assert result["errors"][0]["code"] == "validation_error"


def test_json_payload_requires_email(monkeypatch, capsys):
    monkeypatch.setattr(cli_main, "_load_credentials", lambda: "test-key")
    status = cli_main.main(
        ["people", "upsert", "--json", '{"first_name":"Ada"}']
    )
    result = json.loads(capsys.readouterr().out)
    assert status == 1
    assert result["errors"][0]["code"] == "validation_error"
    assert "email" in result["errors"][0]["message"]


def test_upsert_help_documents_phone_country(capsys):
    with pytest.raises(SystemExit) as exc_info:
        cli_main.main(["people", "upsert", "--help"])
    assert exc_info.value.code == 0
    assert "--phone-country-code" in capsys.readouterr().out


def test_root_help_explains_credential_precedence(capsys):
    with pytest.raises(SystemExit) as exc_info:
        cli_main.main(["--help"])
    assert exc_info.value.code == 0
    output = capsys.readouterr().out
    assert "ATTIO_API_KEY" in output
    assert ".env.local" in output
    assert ".env" in output


def test_missing_email_is_a_usage_error(capsys):
    with pytest.raises(SystemExit) as exc_info:
        cli_main.main(["people", "upsert"])
    assert exc_info.value.code == 2
    assert "email is required" in capsys.readouterr().err


def test_missing_api_key_is_clear_structured_failure(monkeypatch, capsys):
    monkeypatch.setattr(cli_main, "_load_credentials", lambda: None)
    status = cli_main.main(["people", "upsert", "ada@example.com"])
    result = json.loads(capsys.readouterr().out)
    assert status == 1
    assert "ATTIO_API_KEY" in result["errors"][0]["message"]


def test_dotenv_local_precedes_dotenv_but_environment_wins(monkeypatch, tmp_path):
    (tmp_path / ".env.local").write_text(
        "ATTIO_API_KEY=local-key\nHTTPS_PROXY=https://attacker.example\n"
    )
    (tmp_path / ".env").write_text("ATTIO_API_KEY=env-file-key\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ATTIO_API_KEY", raising=False)
    monkeypatch.delenv("HTTPS_PROXY", raising=False)
    assert cli_main._load_credentials() == "local-key"
    assert "HTTPS_PROXY" not in os.environ
    (tmp_path / ".env.local").unlink()
    assert cli_main._load_credentials() == "env-file-key"
    monkeypatch.setenv("ATTIO_API_KEY", "shell-key")
    assert cli_main._load_credentials() == "shell-key"


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ("ATTIO_API_KEY=key with spaces # trailing comment", "key with spaces"),
        ('ATTIO_API_KEY="key with # inside" # trailing comment', "key with # inside"),
        ("export ATTIO_API_KEY='single quoted key'", "single quoted key"),
    ],
)
def test_dotenv_parser_preserves_value_spaces_and_quoted_hashes(
    line, expected, tmp_path
):
    dotenv = tmp_path / ".env"
    dotenv.write_text(line + "\n")
    assert cli_main._dotenv_api_key(dotenv) == expected


@pytest.mark.parametrize(
    ("dotenv_path", "contents", "error_code"),
    [
        (".env.local", None, "credential_file_error"),
        (".env", b"ATTIO_API_KEY=\xff\n", "credential_file_error"),
        (".env.local", b'ATTIO_API_KEY="unterminated\n', "invalid_dotenv"),
    ],
)
def test_bad_dotenv_files_return_structured_failures(
    monkeypatch, tmp_path, capsys, dotenv_path, contents, error_code
):
    target = tmp_path / dotenv_path
    if contents is None:
        target.mkdir()
    else:
        target.write_bytes(contents)
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ATTIO_API_KEY", raising=False)

    status = cli_main.main(["people", "upsert", "ada@example.com"])
    result = json.loads(capsys.readouterr().out)
    assert status == 1
    assert result["errors"][0]["code"] == error_code


def test_empty_credentials_fall_through_to_next_source(monkeypatch, tmp_path):
    (tmp_path / ".env.local").write_text('ATTIO_API_KEY="  "\n')
    (tmp_path / ".env").write_text("export ATTIO_API_KEY='file-key' # comment\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ATTIO_API_KEY", "  ")
    assert cli_main._load_credentials() == "file-key"
    monkeypatch.delenv("ATTIO_API_KEY")
    assert cli_main._load_credentials() == "file-key"


def test_error_envelope_has_versioned_shape():
    result = error_envelope(CLIError("test_error", "A clear message"))
    assert result["meta"] == {"output_schema_version": "v1"}
    assert result["errors"][0]["message"] == "A clear message"


def test_invalid_api_key_error_is_actionable():
    exc = RuntimeError('{"status_code": 401, "code": "unauthorized"}')
    result = error_envelope(exc)
    assert result["errors"][0]["code"] == "invalid_api_key"
    assert "record read/write scopes" in result["errors"][0]["message"]


@pytest.mark.parametrize(
    ("status_code", "code"),
    [
        (204, "no_content"),
        (400, "validation_type"),
        (429, "rate_limited"),
        (500, "server_error"),
    ],
)
def test_error_envelope_preserves_non_auth_api_errors(status_code, code):
    exc = RuntimeError(
        json.dumps(
            {
                "status_code": status_code,
                "type": "invalid_request_error",
                "code": code,
                "message": "Attio request failed.",
            }
        )
    )
    result = error_envelope(exc)
    assert result["errors"][0]["status_code"] == status_code
    assert result["errors"][0]["code"] == code
