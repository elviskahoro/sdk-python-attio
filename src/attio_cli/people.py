"""People upsert behavior and Attio value normalization."""

from __future__ import annotations

import ipaddress
import json
import re
from collections.abc import Callable, Mapping, Sequence
from typing import Any, Literal

from attio import SDK

from .query import PersonUpsertQuery

OPTIONAL_FIELD_WARNING_CODES = {
    "associated_company": "attio_associated_company_field_unavailable",
    "company": "attio_associated_company_field_unavailable",
    "notes": "attio_notes_field_unavailable",
    "primary_location": "attio_location_field_unavailable",
}
OPTIONAL_FIELD_ALIASES = {"associated_company": "company", "company": "associated_company"}
RECORD_QUERY_LIMIT = 50
PARTIAL_WARNING_CODES = {
    "upsert_multi_match_selected_record",
    "upsert_multi_match_result_limit_reached",
}

_DOMAIN_LABEL_RE = re.compile(r"^(?=.{1,63}$)[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?$")
_LINKEDIN_PROFILE_RE = re.compile(
    r"^https?://(?:www\.)?linkedin\.com/in/([^/?#]+)", re.IGNORECASE
)
_LINKEDIN_HANDLE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")


class CLIError(Exception):
    """A safe, user-facing CLI error with a stable envelope code."""

    def __init__(self, code: str, message: str, *, field: str | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.field = field


def normalize_emails(candidates: Sequence[str | None]) -> list[str]:
    """Strip and case-insensitively deduplicate email addresses."""
    result: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        if candidate is None:
            continue
        email = str(candidate).strip()
        if not email or email.casefold() in seen:
            continue
        seen.add(email.casefold())
        result.append(email)
    return result


def _format_name(first_name: str | None, last_name: str | None) -> list[dict[str, str]] | None:
    if not first_name and not last_name:
        return None
    parts = [part for part in (first_name, last_name) if part]
    return [
        {
            "first_name": first_name or "",
            "last_name": last_name or "",
            "full_name": " ".join(parts),
        }
    ]


def _format_phone(
    phone: str | None, country_code: str | None
) -> list[dict[str, str]] | None:
    if not phone:
        return None
    normalized_phone = phone.strip()
    value = {"original_phone_number": normalized_phone}
    if not normalized_phone.startswith("+"):
        if not country_code:
            return None
        value["country_code"] = country_code.upper()
    return [value]


def _format_linkedin(value: str | None) -> list[str] | None:
    if not value:
        return None
    candidate = value.strip()
    match = _LINKEDIN_PROFILE_RE.match(candidate)
    if match:
        return [f"https://www.linkedin.com/in/{match.group(1).rstrip('/')}"]
    if "://" in candidate or "/" in candidate or not _LINKEDIN_HANDLE_RE.fullmatch(candidate):
        return None
    return [f"https://www.linkedin.com/in/{candidate.rstrip('/')}"]


def _format_domain(domain: str | None) -> str | None:
    if not domain:
        return None
    normalized = domain.strip().lower()
    if not normalized or len(normalized) > 253 or "." not in normalized:
        return None
    try:
        ipaddress.IPv4Address(normalized)
    except ValueError:
        pass
    else:
        return None
    if not all(_DOMAIN_LABEL_RE.fullmatch(label) for label in normalized.split(".")):
        return None
    return normalized


def _build_core_values(
    query: PersonUpsertQuery,
    *,
    partial: bool = False,
    email_addresses: list[str] | None = None,
) -> dict[str, Any]:
    values: dict[str, Any] = {}
    if email_addresses is not None:
        normalized = normalize_emails(email_addresses)
        if normalized:
            values["email_addresses"] = [{"email_address": item} for item in normalized]
    elif not partial:
        normalized = normalize_emails([query.email, *query.additional_emails])
        if normalized:
            values["email_addresses"] = [{"email_address": item} for item in normalized]

    name = _format_name(query.first_name, query.last_name)
    if name:
        values["name"] = name
    if query.job_title:
        values["job_title"] = [query.job_title]
    phone = _format_phone(query.phone, query.phone_country_code)
    if phone:
        values["phone_numbers"] = phone
    linkedin = _format_linkedin(query.linkedin)
    if linkedin:
        values["linkedin"] = linkedin
    return values


def _build_optional_values(query: PersonUpsertQuery) -> dict[str, Any]:
    values: dict[str, Any] = {}
    domain = _format_domain(query.company_domain)
    if domain:
        values["associated_company"] = [
            {"target_object": "companies", "domains": [{"domain": domain}]}
        ]
    if query.location and query.country_code:
        parts = query.location.split(",")
        if query.location_mode == "raw":
            line_1 = parts[0].strip() if parts else None
            locality = parts[1].strip() if len(parts) > 1 else None
            region = parts[2].strip() if len(parts) > 2 else None
        else:
            line_1 = None
            locality = parts[0].strip() if parts else None
            region = parts[1].strip() if len(parts) > 1 else None
        values["primary_location"] = [
            {
                "line_1": line_1,
                "line_2": None,
                "line_3": None,
                "line_4": None,
                "locality": locality,
                "region": region,
                "postcode": None,
                "country_code": query.country_code.upper(),
                "latitude": None,
                "longitude": None,
            }
        ]
    if query.notes:
        values["notes"] = [query.notes]
    return values


def _validation_warnings(
    query: PersonUpsertQuery,
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    invalid: list[tuple[str, str]] = []
    if query.linkedin is not None and _format_linkedin(query.linkedin) is None:
        invalid.append(("linkedin", "LinkedIn value must be a profile URL or handle."))
    if query.company_domain is not None and _format_domain(query.company_domain) is None:
        invalid.append(("company_domain", "Company value must be a valid domain."))
    if query.country_code is not None and not query.location:
        invalid.append(("country_code", "country_code is only used with --location."))
    if query.phone is not None and not query.phone.strip():
        invalid.append(("phone", "Phone number must not be empty."))
    elif query.phone and not query.phone.strip().startswith("+") and not query.phone_country_code:
        invalid.append(
            (
                "phone",
                "A local phone number requires --phone-country-code; use +country format otherwise.",
            )
        )
    if query.phone_country_code is not None and (
        not query.phone or query.phone.strip().startswith("+")
    ):
        invalid.append(
            ("phone_country_code", "phone_country_code is only used with local phone numbers.")
        )

    warnings: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    for field, message in invalid:
        if query.strict:
            raise CLIError("invalid_value", message, field=field)
        warnings.append(
            {
                "code": "invalid_value",
                "message": f"Skipped invalid value for '{field}': {message}",
                "field": field,
                "retryable": False,
            }
        )
        skipped.append({"field": field, "reason": "invalid_value"})
    return warnings, skipped


def _error_body(exc: BaseException) -> str:
    body = getattr(exc, "body", None)
    if body is None:
        return str(exc)
    if isinstance(body, bytes):
        return body.decode("utf-8", errors="replace")
    if isinstance(body, str):
        return body
    if hasattr(body, "model_dump"):
        body = body.model_dump()
    try:
        return json.dumps(body, default=str)
    except (TypeError, ValueError):
        return str(body)


def _detect_optional_field(exc: BaseException) -> str | None:
    """Recognize Attio's explicit missing-attribute response, not arbitrary mentions."""
    try:
        payload = json.loads(_error_body(exc))
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(payload, Mapping):
        return None

    status_code = getattr(exc, "status_code", None)
    if status_code is None:
        status_code = payload.get("status_code")
    if (
        status_code != 404
        or payload.get("type") != "invalid_request_error"
        or payload.get("code") != "not_found"
        or not isinstance(payload.get("message"), str)
    ):
        return None

    message = payload["message"]
    for field in OPTIONAL_FIELD_WARNING_CODES:
        not_found_pattern = (
            rf"\battribute(?:\s+with\s+slug/id)?\s+['\"]?{re.escape(field)}"
            rf"['\"]?\s+(?:was\s+)?not found\b"
        )
        cannot_find_pattern = (
            rf"\b(?:cannot|could not)\s+find\s+attribute"
            rf"(?:\s+with\s+slug/id)?\s+['\"]?{re.escape(field)}['\"]?(?=\s|[.!]|$)"
        )
        if re.search(not_found_pattern, message, flags=re.IGNORECASE) or re.search(
            cannot_find_pattern, message, flags=re.IGNORECASE
        ):
            return field
    return None


def _is_uniqueness_conflict(exc: BaseException) -> bool:
    try:
        payload = json.loads(_error_body(exc))
    except (json.JSONDecodeError, TypeError):
        return "uniqueness_conflict" in _error_body(exc)
    return isinstance(payload, Mapping) and payload.get("code") == "uniqueness_conflict"


def _uniqueness_conflict_error(exc: BaseException, query: PersonUpsertQuery) -> CLIError:
    candidates = normalize_emails([query.email, *query.additional_emails])
    body = _error_body(exc).casefold()
    conflicting = next(
        (email for email in candidates if email.casefold() in body),
        None,
    )
    if conflicting:
        message = (
            f"Email address '{conflicting}' already belongs to another person. "
            "Remove it from the requested addresses and retry."
        )
    else:
        addresses = ", ".join(f"'{email}'" for email in candidates)
        message = (
            "One or more requested email addresses conflict with another person: "
            f"{addresses}. Remove the conflicting address and retry."
        )
    return CLIError("uniqueness_conflict", message)


def _write_with_optional_fallback(
    write: Callable[[dict[str, Any]], Any],
    core_values: dict[str, Any],
    optional_values: dict[str, Any],
    *,
    strict: bool,
) -> tuple[Any, list[dict[str, Any]], list[dict[str, str]]]:
    active = dict(optional_values)
    attempted_aliases: set[frozenset[str]] = set()
    warnings: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    while True:
        try:
            response = write({**core_values, **active})
        except Exception as exc:
            field = _detect_optional_field(exc)
            if field is None:
                raise
            if strict:
                raise CLIError(
                    "schema_mismatch",
                    f"Optional field unavailable in this Attio workspace: {field}",
                    field=field,
                ) from exc

            alias = OPTIONAL_FIELD_ALIASES.get(field)
            if field not in active and alias in active:
                field, alias = alias, field
            if alias and field in active and alias not in active:
                pair = frozenset((field, alias))
                if pair not in attempted_aliases:
                    attempted_aliases.add(pair)
                    active[alias] = active.pop(field)
                    continue
            if field not in active:
                raise
            del active[field]
            warnings.append(
                {
                    "code": OPTIONAL_FIELD_WARNING_CODES[field],
                    "message": f"Skipped optional field '{field}' due to schema mismatch.",
                    "field": field,
                    "retryable": False,
                }
            )
            skipped.append({"field": field, "reason": "schema_mismatch"})
        else:
            return response, warnings, skipped


def _emails_from_record(record: Any) -> list[str]:
    emails: list[str] = []
    for value in getattr(record, "values", {}).get("email_addresses", []):
        email = getattr(value, "email_address", None)
        if email:
            emails.append(email)
    return emails


def _person_meta(record: Any, *, created: bool) -> dict[str, Any]:
    record_id = record.id.record_id
    values = getattr(record, "values", {})
    name = None
    for name_value in values.get("name", []):
        name = getattr(name_value, "full_name", None)
        if name:
            break
    return {
        "record_id": record_id,
        "email_addresses": _emails_from_record(record),
        "name": name,
        "created": created,
        "raw": {},
    }


def _result_envelope(
    *,
    action: Literal["created", "updated"],
    record: Any,
    warnings: list[dict[str, Any]],
    skipped: list[dict[str, str]],
) -> dict[str, Any]:
    created = action == "created"
    return {
        "success": True,
        "partial_success": bool(skipped)
        or any(warning["code"] in PARTIAL_WARNING_CODES for warning in warnings),
        "action": action,
        "record_id": record.id.record_id,
        "warnings": warnings,
        "skipped_fields": skipped,
        "errors": [],
        "meta": {"output_schema_version": "v1", "person": _person_meta(record, created=created)},
    }


def _record_id(item: Any) -> str:
    return str(item.id.record_id)


def _record_name_parts(record: Any) -> tuple[str | None, str | None]:
    values = getattr(record, "values", {})
    name = next(iter(values.get("name", [])), None)
    if isinstance(name, Mapping):
        first_name = name.get("first_name")
        last_name = name.get("last_name")
        full_name = name.get("full_name")
    else:
        first_name = getattr(name, "first_name", None)
        last_name = getattr(name, "last_name", None)
        full_name = getattr(name, "full_name", None)
    if first_name is None and last_name is None and isinstance(full_name, str):
        parts = full_name.split(maxsplit=1)
        first_name = parts[0] if parts else None
        last_name = parts[1] if len(parts) > 1 else None
    return first_name, last_name


def upsert_person(query: PersonUpsertQuery, client: Any) -> dict[str, Any]:
    """Search by email, then create/update with upstream reliability semantics."""
    warnings, skipped = _validation_warnings(query)
    response = client.records.post_v2_objects_object_records_query(
        object="people",
        filter_={"email_addresses": query.email.strip()},
        limit=RECORD_QUERY_LIMIT,
    )
    matches = list(response.data)
    if len(matches) == 0:
        action: Literal["created", "updated"] = "created"
        core = _build_core_values(query)
        optional = _build_optional_values(query)

        def create(values: dict[str, Any]) -> Any:
            return client.records.post_v2_objects_object_records(
                object="people",
                data={"values": values},
            )

        try:
            written, write_warnings, write_skipped = _write_with_optional_fallback(
                create, core, optional, strict=query.strict
            )
            skipped.extend(write_skipped)
        except Exception as exc:
            if _is_uniqueness_conflict(exc):
                raise _uniqueness_conflict_error(exc, query) from None
            raise
    else:
        if len(matches) > 1:
            if query.strict:
                raise CLIError(
                    "multiple_matches",
                    f"Multiple people matched email {query.email}; strict mode rejects ambiguity.",
                )
            selected = sorted(matches, key=_record_id)[0]
            warnings.append(
                {
                    "code": "upsert_multi_match_selected_record",
                    "message": (
                        "Multiple records matched; wrote to the lexicographically smallest "
                        "record_id. Other duplicates were left in place for manual review."
                    ),
                    "field": "record_id",
                    "retryable": False,
                }
            )
            if len(matches) == RECORD_QUERY_LIMIT:
                warnings.append(
                    {
                        "code": "upsert_multi_match_result_limit_reached",
                        "message": (
                            f"The email search reached its {RECORD_QUERY_LIMIT}-record limit; "
                            "the selected record is the smallest ID in the returned results, "
                            "and additional matches may exist."
                        ),
                        "field": "record_id",
                        "retryable": False,
                    }
                )
        else:
            selected = matches[0]
        record_id = _record_id(selected)
        existing = client.records.get_v2_objects_object_records_record_id_(
            object="people", record_id=record_id
        )
        existing_emails = _emails_from_record(existing.data)
        email_write: list[str] | None = None
        if query.replace_emails:
            email_write = normalize_emails([query.email, *query.additional_emails])
            if {email.casefold() for email in email_write} != {
                email.casefold() for email in existing_emails
            }:
                warnings.append(
                    {
                        "code": "multiple_emails_added",
                        "message": "Email addresses updated (--replace-emails).",
                        "field": "email_addresses",
                        "retryable": False,
                    }
                )
        elif query.additional_emails:
            email_write = normalize_emails(
                [*existing_emails, query.email, *query.additional_emails]
            )
            new = {email.casefold() for email in email_write} - {
                email.casefold() for email in existing_emails
            }
            if new:
                warnings.append(
                    {
                        "code": "multiple_emails_added",
                        "message": "New email address(es) merged onto existing person.",
                        "field": "email_addresses",
                        "retryable": False,
                    }
                )

        action = "updated"
        core = _build_core_values(query, partial=True, email_addresses=email_write)
        if query.first_name is not None or query.last_name is not None:
            existing_first_name, existing_last_name = _record_name_parts(existing.data)
            first_name = (
                query.first_name if query.first_name is not None else existing_first_name
            )
            last_name = (
                query.last_name if query.last_name is not None else existing_last_name
            )
            merged_name = _format_name(first_name, last_name)
            if merged_name:
                core["name"] = merged_name
        optional = _build_optional_values(query)

        def update(values: dict[str, Any]) -> Any:
            return client.records.put_v2_objects_object_records_record_id_(
                object="people",
                record_id=record_id,
                data={"values": values},
            )

        try:
            written, write_warnings, write_skipped = _write_with_optional_fallback(
                update, core, optional, strict=query.strict
            )
            skipped.extend(write_skipped)
        except Exception as exc:
            if _is_uniqueness_conflict(exc):
                raise _uniqueness_conflict_error(exc, query) from None
            raise

    warnings.extend(write_warnings)
    return _result_envelope(
        action=action,
        record=written.data,
        warnings=warnings,
        skipped=skipped,
    )


def error_envelope(exc: BaseException) -> dict[str, Any]:
    """Convert validation, auth, and API failures into the stable JSON shape."""
    code = getattr(exc, "code", "attio_error")
    field = getattr(exc, "field", None)
    status_code = getattr(exc, "status_code", None)
    body_text = _error_body(exc)
    details: dict[str, Any] = {}
    attio_type = None
    message = str(exc).strip() or exc.__class__.__name__
    try:
        body = json.loads(body_text)
    except (json.JSONDecodeError, TypeError):
        body = None
    if isinstance(body, Mapping):
        body_status = body.get("status_code")
        if status_code is None and isinstance(body_status, int):
            status_code = body_status
        attio_type = body.get("type") if isinstance(body.get("type"), str) else None
        if isinstance(body.get("code"), str):
            code = body["code"]
        if isinstance(body.get("message"), str):
            message = body["message"]
        if isinstance(body.get("data"), Mapping):
            details = dict(body["data"])
    if status_code in {401, 403} or code == "unauthorized":
        code = "invalid_api_key"
        message = (
            f"Attio rejected ATTIO_API_KEY (HTTP {status_code or '401'}). "
            "Check the key and its record read/write scopes."
        )
    error: dict[str, Any] = {
        "code": code,
        "message": message,
        "error_type": exc.__class__.__name__,
        "fatal": True,
        "field": field,
        "status_code": status_code,
        "type": attio_type,
        "details": details,
    }
    return {
        "success": False,
        "partial_success": False,
        "action": "failed",
        "record_id": None,
        "warnings": [],
        "skipped_fields": [],
        "errors": [error],
        "meta": {"output_schema_version": "v1"},
    }


def execute_upsert(api_key: str, query: PersonUpsertQuery) -> dict[str, Any]:
    """Create a short-lived SDK client and run the upsert."""
    with SDK(oauth2=api_key) as client:
        return upsert_person(query, client)
