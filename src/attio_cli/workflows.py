"""People, company, and note workflows for the standalone CLI."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .people import (
    CLIError,
    RECORD_QUERY_LIMIT,
    _build_core_values,
    _build_optional_values,
    _emails_from_record,
    _format_domain,
    _format_name,
    _is_uniqueness_conflict,
    _record_id,
    _record_name_parts,
    _result_envelope,
    _uniqueness_conflict_error,
    _validation_warnings,
    _write_with_optional_fallback,
    normalize_emails,
)
from .query import (
    CompanyPayload,
    NoteAddPayload,
    NoteListPayload,
    NoteUpdatePayload,
    PersonUpsertQuery,
)


def _success_envelope(
    action: str,
    *,
    record_id: str | None = None,
    results: list[Any] | None = None,
    **meta: Any,
) -> dict[str, Any]:
    metadata: dict[str, Any] = {"output_schema_version": "v1", **meta}
    if results is not None:
        metadata["results"] = [_jsonable(item) for item in results]
    return {
        "success": True,
        "partial_success": False,
        "action": action,
        "record_id": record_id,
        "warnings": [],
        "skipped_fields": [],
        "errors": [],
        "meta": metadata,
    }


def _jsonable(value: Any) -> Any:
    """Convert SDK models and test doubles to JSON-compatible structures."""
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json", by_alias=True)
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if hasattr(value, "__dict__"):
        return {key: _jsonable(item) for key, item in vars(value).items()}
    return value


def _query_records(client: Any, object_name: str, filter_: dict[str, Any]) -> list[Any]:
    response = client.records.post_v2_objects_object_records_query(
        object=object_name,
        filter_=filter_,
        limit=RECORD_QUERY_LIMIT,
    )
    return list(response.data)


def _normalized_email(email: str) -> str:
    normalized = email.strip().casefold()
    if not normalized or "@" not in normalized:
        raise CLIError("validation_error", "email must be a non-empty email address", field="email")
    return normalized


def search_people(email: str, client: Any) -> dict[str, Any]:
    normalized = _normalized_email(email)
    matches = _query_records(client, "people", {"email_addresses": normalized})
    result = _success_envelope("searched", results=matches, identity={"email": normalized})
    if len(matches) == RECORD_QUERY_LIMIT:
        result["partial_success"] = True
        result["warnings"].append(
            {
                "code": "search_result_limit_reached",
                "message": f"The search returned its {RECORD_QUERY_LIMIT}-record limit; additional matches may exist.",
                "field": "email",
                "retryable": False,
            }
        )
    return result


def add_person(query: PersonUpsertQuery, client: Any) -> dict[str, Any]:
    email = query.email.strip()
    normalized = _normalized_email(email)
    query = query.model_copy(update={"email": email})
    matches = _query_records(client, "people", {"email_addresses": normalized})
    if matches:
        raise CLIError(
            "duplicate_identity",
            f"A person already matches email '{normalized}'; use people update or people upsert.",
            field="email",
        )

    warnings, skipped = _validation_warnings(query)
    core = _build_core_values(query)
    optional = _build_optional_values(query)

    def create(values: dict[str, Any]) -> Any:
        return client.records.post_v2_objects_object_records(
            object="people", data={"values": values}
        )

    try:
        response, write_warnings, write_skipped = _write_with_optional_fallback(
            create, core, optional, strict=query.strict
        )
    except Exception as exc:
        if _is_uniqueness_conflict(exc):
            conflict = _uniqueness_conflict_error(exc, query)
            raise CLIError(
                "duplicate_identity", str(conflict), field="email"
            ) from None
        raise
    return _result_envelope(
        action="created",
        record=response.data,
        warnings=[*warnings, *write_warnings],
        skipped=[*skipped, *write_skipped],
    )


def update_person(query: PersonUpsertQuery, client: Any) -> dict[str, Any]:
    email = query.email.strip()
    normalized = _normalized_email(email)
    query = query.model_copy(update={"email": email})
    has_changes = any(
        value is not None
        for value in (
            query.first_name,
            query.last_name,
            query.job_title,
            query.phone,
            query.phone_country_code,
            query.linkedin,
            query.location,
            query.country_code,
            query.company_domain,
            query.notes,
        )
    ) or bool(query.additional_emails) or query.replace_emails
    if not has_changes:
        raise CLIError(
            "validation_error",
            "provide at least one field to update in addition to the email identity.",
        )
    warnings, skipped = _validation_warnings(query)
    matches = _query_records(client, "people", {"email_addresses": normalized})
    if not matches:
        raise CLIError("record_not_found", f"No person matches email '{normalized}'.", field="email")
    if len(matches) != 1:
        raise CLIError(
            "multiple_matches",
            f"{len(matches)} people match email '{normalized}'; update was not applied.",
            field="email",
        )

    record_id = _record_id(matches[0])
    existing = client.records.get_v2_objects_object_records_record_id_(
        object="people", record_id=record_id
    ).data

    email_write: list[str] | None = None
    if query.replace_emails:
        email_write = normalize_emails([email, *query.additional_emails])
    elif query.additional_emails:
        email_write = normalize_emails(
            [*_emails_from_record(existing), email, *query.additional_emails]
        )

    core = _build_core_values(query, partial=True, email_addresses=email_write)
    if query.first_name is not None or query.last_name is not None:
        existing_first, existing_last = _record_name_parts(existing)
        name = _format_name(
            query.first_name if query.first_name is not None else existing_first,
            query.last_name if query.last_name is not None else existing_last,
        )
        if name:
            core["name"] = name
    optional = _build_optional_values(query)
    if not core and not optional:
        raise CLIError(
            "validation_error",
            "No valid person fields were supplied for the update.",
        )

    def update(values: dict[str, Any]) -> Any:
        return client.records.put_v2_objects_object_records_record_id_(
            object="people", record_id=record_id, data={"values": values}
        )

    try:
        response, write_warnings, write_skipped = _write_with_optional_fallback(
            update, core, optional, strict=query.strict
        )
    except Exception as exc:
        if _is_uniqueness_conflict(exc):
            raise _uniqueness_conflict_error(exc, query) from None
        raise
    return _result_envelope(
        action="updated",
        record=response.data,
        warnings=[*warnings, *write_warnings],
        skipped=[*skipped, *write_skipped],
    )


def _company_domain(value: str) -> str:
    normalized = _format_domain(value)
    if normalized is None:
        raise CLIError(
            "validation_error",
            "domain must be a valid fully qualified company domain.",
            field="domain",
        )
    return normalized


def _company_values(payload: CompanyPayload, domain: str) -> dict[str, list[Any]]:
    values = {key: list(value) for key, value in payload.values.items()}
    values["domains"] = [{"domain": domain}]
    return values


def search_companies(payload: CompanyPayload, client: Any) -> dict[str, Any]:
    domain = _company_domain(payload.domain)
    matches = _query_records(client, "companies", {"domains": domain})
    result = _success_envelope("searched", results=matches, identity={"domain": domain})
    if len(matches) == RECORD_QUERY_LIMIT:
        result["partial_success"] = True
        result["warnings"].append(
            {
                "code": "search_result_limit_reached",
                "message": f"The search returned its {RECORD_QUERY_LIMIT}-record limit; additional matches may exist.",
                "field": "domain",
                "retryable": False,
            }
        )
    return result


def add_company(payload: CompanyPayload, client: Any) -> dict[str, Any]:
    domain = _company_domain(payload.domain)
    matches = _query_records(client, "companies", {"domains": domain})
    if matches:
        raise CLIError(
            "duplicate_identity",
            f"A company already matches domain '{domain}'; use companies update.",
            field="domain",
        )
    try:
        response = client.records.post_v2_objects_object_records(
            object="companies", data={"values": _company_values(payload, domain)}
        )
    except Exception as exc:
        if _is_uniqueness_conflict(exc):
            raise CLIError(
                "duplicate_identity",
                f"A company already owns domain '{domain}'; no company was created.",
                field="domain",
            ) from None
        raise
    record = response.data
    return _success_envelope(
        "created", record_id=_record_id(record), company=_jsonable(record), domain=domain
    )


def update_company(payload: CompanyPayload, client: Any) -> dict[str, Any]:
    domain = _company_domain(payload.domain)
    if not payload.values:
        raise CLIError(
            "validation_error",
            "provide at least one company attribute in values to update.",
            field="values",
        )
    matches = _query_records(client, "companies", {"domains": domain})
    if not matches:
        raise CLIError("record_not_found", f"No company matches domain '{domain}'.", field="domain")
    if len(matches) != 1:
        raise CLIError(
            "multiple_matches",
            f"{len(matches)} companies match domain '{domain}'; update was not applied.",
            field="domain",
        )
    record_id = _record_id(matches[0])
    # The matching domain is only the lookup key. Omitting it from the write
    # preserves any other domains on the company while PUT replaces supplied
    # multiselect attributes instead of appending duplicate values.
    response = client.records.put_v2_objects_object_records_record_id_(
        object="companies",
        record_id=record_id,
        data={"values": {key: list(value) for key, value in payload.values.items()}},
    )
    record = response.data
    return _success_envelope(
        "updated", record_id=_record_id(record), company=_jsonable(record), domain=domain
    )


def list_notes(payload: NoteListPayload, client: Any) -> dict[str, Any]:
    response = client.notes.get_v2_notes(
        parent_object=payload.parent_object,
        parent_record_id=payload.parent_record_id,
        limit=payload.limit,
        offset=payload.offset,
    )
    return _success_envelope(
        "listed",
        results=list(response.data),
        parent={
            "object": payload.parent_object,
            "record_id": payload.parent_record_id,
        },
        limit=payload.limit,
        offset=payload.offset,
    )


def add_note(payload: NoteAddPayload, client: Any) -> dict[str, Any]:
    response = client.notes.post_v2_notes(
        data={
            "parent_object": payload.parent_object,
            "parent_record_id": payload.parent_record_id,
            "title": payload.title,
            "content": payload.content,
            "format_": payload.format,
        }
    )
    note = response.data
    note_id = note.id.note_id
    return _success_envelope(
        "created", record_id=note_id, note_id=note_id, note=_jsonable(note)
    )


def update_note(payload: NoteUpdatePayload, client: Any) -> dict[str, Any]:
    data = payload.model_dump(exclude={"note_id"}, exclude_none=True, by_alias=True)
    response = client.notes.patch_v2_notes_note_id_(note_id=payload.note_id, data=data)
    note = response.data
    note_id = note.id.note_id
    return _success_envelope(
        "updated", record_id=note_id, note_id=note_id, note=_jsonable(note)
    )
