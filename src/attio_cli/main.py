"""Entry point for the standalone ``gtm-attio`` command."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Sequence

from pydantic import ValidationError

from attio import SDK
from attio._version import __version__

from .people import CLIError, error_envelope, execute_upsert
from .query import (
    CompanyPayload,
    NoteAddPayload,
    NoteListPayload,
    NoteUpdatePayload,
    PersonUpsertQuery,
)
from .workflows import (
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


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gtm-attio",
        description="A standalone Attio CLI for agent-friendly people, company, and note workflows.",
        epilog=(
            "Credentials: ATTIO_API_KEY from the process environment takes priority, "
            "then .env.local and .env in the current working directory."
        ),
    )
    parser.add_argument("--version", action="version", version=f"gtm-attio {__version__}")
    groups = parser.add_subparsers(dest="resource", required=True)
    people = groups.add_parser("people", help="Manage people records")
    people_commands = people.add_subparsers(dest="operation", required=True)

    search = people_commands.add_parser(
        "search", help="Find people by exact email", description="Read-only search by email."
    )
    search.add_argument("email", help="Email address to find")

    for operation, summary in (
        ("upsert", "Create or update a person using email as the identity key"),
        ("add", "Create a person; fail if the email already exists"),
        ("update", "Update exactly one person matching the email"),
    ):
        command = people_commands.add_parser(
            operation,
            help=summary,
            description=f"{summary}. Writes are applied immediately.",
        )
        command.add_argument(
            "email",
            nargs="?",
            help="Email identity (unless --json supplies an email field)",
        )
        command.add_argument(
            "--add-email",
            action="append",
            dest="additional_emails",
            default=None,
            help="Extra email to store; repeat for multiple addresses",
        )
        if operation != "add":
            command.add_argument(
                "--replace-emails",
                action="store_true",
                help="On update, replace stored emails with the identity and --add-email values",
            )
        command.add_argument("--first-name", help="First name")
        command.add_argument("--last-name", help="Last name")
        command.add_argument("--job-title", help="Job title")
        command.add_argument("--phone", help="Phone number; use +country prefix or --phone-country-code")
        command.add_argument("--phone-country-code", help="ISO-3166-1 alpha-2 code for a local phone number")
        command.add_argument("--linkedin", help="LinkedIn profile URL or handle")
        command.add_argument("--location", help="Primary location")
        command.add_argument("--country-code", help="ISO-3166-1 alpha-2 code required with --location")
        command.add_argument("--company", dest="company_domain", help="Company domain")
        command.add_argument("--notes", help="Notes to store on the person")
        command.add_argument("--strict", action="store_true", help="Fail on invalid values or unavailable optional attributes")
        command.add_argument(
            "--location-mode", choices=("city", "raw"), default="city",
            help="Map --location as locality/region (city) or street/locality/region (raw)",
        )
        command.add_argument(
            "--json", dest="json_payload", metavar="PAYLOAD",
            help="Validated JSON input object; when provided it overrides all flags",
        )

    companies = groups.add_parser("companies", help="Manage company records")
    company_commands = companies.add_subparsers(dest="operation", required=True)
    for operation, summary in (
        ("search", "Search by exact domain"),
        ("add", "Create a company; fail if the domain already exists"),
        ("update", "Update exactly one company matching the domain"),
    ):
        command = company_commands.add_parser(
            operation,
            help=summary,
            description=f"{summary}. JSON input is validated; writes are applied immediately.",
        )
        command.add_argument("--json", dest="json_payload", required=True, metavar="PAYLOAD")

    notes = groups.add_parser("notes", help="Manage notes on records")
    note_commands = notes.add_subparsers(dest="operation", required=True)
    for operation, summary in (
        ("list", "List notes attached to a record"),
        ("add", "Create a note on a record"),
        ("update", "Update a note by ID"),
    ):
        command = note_commands.add_parser(
            operation,
            help=summary,
            description=f"{summary}. JSON input is validated; writes are applied immediately.",
        )
        command.add_argument("--json", dest="json_payload", required=True, metavar="PAYLOAD")
    return parser


def _validation_message(exc: ValidationError) -> str:
    messages = []
    for error in exc.errors(include_url=False):
        location = ".".join(str(part) for part in error.get("loc", ()))
        message = str(error.get("msg", "Invalid value"))
        messages.append(f"{location}: {message}" if location else message)
    return "; ".join(messages)


def _dotenv_api_key(path: Path) -> str | None:
    """Read only ATTIO_API_KEY from a dotenv file without changing the environment."""
    try:
        lines = path.read_text().splitlines()
    except FileNotFoundError:
        return None
    except (OSError, UnicodeDecodeError) as exc:
        raise CLIError(
            "credential_file_error",
            f"Could not read {path.name}: {exc.__class__.__name__}.",
        ) from None
    for line_number, line in enumerate(lines, start=1):
        candidate = line.strip()
        if candidate.startswith("export") and len(candidate) > 6 and candidate[6].isspace():
            candidate = candidate[6:].lstrip()
        name, separator, raw_value = candidate.partition("=")
        if not separator or name.strip() != "ATTIO_API_KEY":
            continue
        value = raw_value.lstrip()
        if value.startswith(("'", '"')):
            quote = value[0]
            end = 1
            escaped = False
            while end < len(value):
                char = value[end]
                if char == quote and not escaped:
                    break
                escaped = char == "\\" and not escaped
                end += 1
            if end == len(value):
                raise CLIError(
                    "invalid_dotenv",
                    f"{path.name}:{line_number} has an unterminated ATTIO_API_KEY value.",
                    field="ATTIO_API_KEY",
                )
            trailing = value[end + 1 :].strip()
            if trailing and not trailing.startswith("#"):
                raise CLIError(
                    "invalid_dotenv",
                    f"{path.name}:{line_number} has unexpected text after ATTIO_API_KEY.",
                    field="ATTIO_API_KEY",
                )
            parsed = value[1:end]
            if quote == '"':
                escapes = {"\\": "\\", '"': '"', "n": "\n", "r": "\r", "t": "\t"}
                parsed = re.sub(
                    r'\\([\\"nrt])',
                    lambda match, escape_map=escapes: escape_map[match.group(1)],
                    parsed,
                )
            else:
                parsed = parsed.replace("\\'", "'").replace("\\\\", "\\")
            return parsed
        comment = re.search(r"(?:^|\s)#", value)
        if comment:
            value = value[: comment.start()]
        return value.rstrip()
    return None


def _load_credentials() -> str | None:
    """Read only the Attio key, preferring the environment and local dotenv files."""
    value = os.environ.get("ATTIO_API_KEY")
    if value and value.strip():
        return value.strip()

    cwd = Path.cwd()
    for dotenv_path in (cwd / ".env.local", cwd / ".env"):
        value = _dotenv_api_key(dotenv_path)
        if value and value.strip():
            return value.strip()
    return None


def _emit(envelope: dict[str, object]) -> None:
    print(json.dumps(envelope, ensure_ascii=False, indent=2))


def _input_from_args(args: argparse.Namespace) -> PersonUpsertQuery:
    if args.json_payload is not None:
        return PersonUpsertQuery.model_validate_json(args.json_payload)
    if not args.email:
        raise CLIError(
            "missing_email",
            "email is required unless --json supplies an email field.",
            field="email",
        )
    return PersonUpsertQuery.model_validate(
        {
            "email": args.email,
            "additional_emails": args.additional_emails or [],
            "replace_emails": getattr(args, "replace_emails", False),
            "first_name": args.first_name,
            "last_name": args.last_name,
            "job_title": args.job_title,
            "phone": args.phone,
            "phone_country_code": args.phone_country_code,
            "linkedin": args.linkedin,
            "location": args.location,
            "country_code": args.country_code,
            "company_domain": args.company_domain,
            "notes": args.notes,
            "strict": args.strict,
            "location_mode": args.location_mode,
        }
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    result: dict[str, Any] | None = None
    try:
        payload: Any
        if args.resource == "people":
            if args.operation == "search":
                payload = PersonUpsertQuery(email=args.email)
            else:
                if args.json_payload is None and not args.email:
                    parser.error("email is required unless --json supplies an email field")
                payload = _input_from_args(args)
        elif args.resource == "companies":
            payload = CompanyPayload.model_validate_json(args.json_payload)
        elif args.operation == "list":
            payload = NoteListPayload.model_validate_json(args.json_payload)
        elif args.operation == "add":
            payload = NoteAddPayload.model_validate_json(args.json_payload)
        else:
            payload = NoteUpdatePayload.model_validate_json(args.json_payload)
    except ValidationError as exc:
        is_bad_json = any(error.get("type") == "json_invalid" for error in exc.errors())
        code = "invalid_json" if is_bad_json else "validation_error"
        _emit(error_envelope(CLIError(code, _validation_message(exc))))
        return 1
    except CLIError as exc:
        _emit(error_envelope(exc))
        return 1
    except (ValueError, json.JSONDecodeError) as exc:
        _emit(error_envelope(CLIError("invalid_json", str(exc))))
        return 1

    try:
        api_key = _load_credentials()
    except CLIError as exc:
        _emit(error_envelope(exc))
        return 1
    if not api_key:
        _emit(
            error_envelope(
                CLIError(
                    "missing_api_key",
                    "ATTIO_API_KEY is not set. Export it or add it to .env.local or .env in the current directory.",
                )
            )
        )
        return 1

    try:
        if args.resource == "people" and args.operation == "upsert":
            result = execute_upsert(api_key, payload)
        else:
            with SDK(oauth2=api_key) as client:
                if args.resource == "people":
                    if args.operation == "search":
                        result = search_people(args.email, client)
                    elif args.operation == "add":
                        result = add_person(payload, client)
                    else:
                        result = update_person(payload, client)
                elif args.resource == "companies":
                    if args.operation == "search":
                        result = search_companies(payload, client)
                    elif args.operation == "add":
                        result = add_company(payload, client)
                    else:
                        result = update_company(payload, client)
                elif args.operation == "list":
                    result = list_notes(payload, client)
                elif args.operation == "add":
                    result = add_note(payload, client)
                else:
                    result = update_note(payload, client)
    except Exception as exc:  # API/SDK failures are represented in the envelope.
        _emit(error_envelope(exc))
        return 1
    if result is None:
        _emit(error_envelope(CLIError("unknown_command", "Unsupported command.")))
        return 1
    _emit(result)
    return 0 if result.get("success") else 1


if __name__ == "__main__":
    sys.exit(main())
