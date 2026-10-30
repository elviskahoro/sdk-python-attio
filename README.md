# Attio Python SDK and CLI

[![PyPI](https://img.shields.io/pypi/v/attio)](https://pypi.org/project/attio/)
[![MIT License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

A type-safe Python client for the [Attio REST API](https://docs.attio.com/rest-api/overview) (v2), with a sync and an async variant of every method. It also ships the standalone `attio` CLI, installed under a second name as `gtm-attio`, for people, company and note workflows. The CLI prints JSON for agents and scripts.

- **Package:** `attio` on PyPI. `gtm-attio` is the same code under another distribution name. Requires Python 3.10+.
- **Credentials:** an Attio API key, in `ATTIO_API_KEY`.
- **Where the SDK comes from:** [Speakeasy](https://www.speakeasy.com/) generates it from Attio's OpenAPI spec into `generated/`. Every method has a reference page under [`generated/docs/sdks/`](https://github.com/elviskahoro/sdk-python-attio/tree/main/generated/docs/sdks).

## Quick start for agents

| Goal | Command |
| --- | --- |
| List the CLI commands (no install) | `uvx gtm-attio --help` |
| The same, with the shorter name (0.28.3+) | `uvx attio --help` |
| Pin an exact version | `uvx gtm-attio@0.28.0 --help` |
| Force the newest release | `uvx gtm-attio@latest --help` |
| Run unreleased code from `main` | `uvx --from git+https://github.com/elviskahoro/sdk-python-attio gtm-attio --help` |
| Install the CLI on PATH | `uv tool install attio` |
| Run a script that imports the SDK | `uv run --with attio script.py` |
| Open a Python REPL with the SDK | `uvx --from attio python` |
| Add the SDK to a project | `uv add attio` (or `pip install attio`) |

Rules of thumb:

1. **Credentials.** Put the Attio API key in `ATTIO_API_KEY`. The CLI also reads it from `.env.local` or `.env` in the working directory. Never pass the key as a command-line argument.
2. **CLI output.** The CLI prints exactly one JSON envelope on stdout. Branch on `success`, `errors[].code` and the exit code, not on message text. The one exception is a usage error (exit 2), which goes to stderr as plain text.
3. **CLI writes.** `add`, `update` and `upsert` write to Attio immediately. There is no confirmation prompt and no dry run, so run `search` or `list` first when unsure.
4. **CLI or SDK?** Use the CLI for people, companies and notes keyed by email, domain or record ID. Use the SDK for everything else: lists, entries, tasks, attributes, webhooks, meetings, SQL and so on.
5. **Finding an SDK method.** Derive its name with [Finding the right method](#finding-the-right-method), then open the resource page under [Available Resources and Operations](#available-resources-and-operations). That page has every parameter, an example, the response model and the errors the method raises.

## Table of Contents

* [Quick start for agents](#quick-start-for-agents)
* [SDK Installation](#sdk-installation)
* [Standalone CLI](#standalone-cli)
* [Authentication](#authentication)
* [SDK Example Usage](#sdk-example-usage)
  * [Finding the right method](#finding-the-right-method)
  * [Record values](#record-values)
* [Common Workflows](#common-workflows)
* [Available Resources and Operations](#available-resources-and-operations)
* [File uploads](#file-uploads)
* [Retries and timeouts](#retries-and-timeouts)
* [Error Handling](#error-handling)
* [Server Selection](#server-selection)
* [Custom HTTP Client](#custom-http-client)
* [Resource Management](#resource-management)
* [Debugging](#debugging)
* [Troubleshooting](#troubleshooting)
* [Maintaining this repository](#maintaining-this-repository)

## SDK Installation

```bash
uv add attio        # or: pip install attio / poetry add attio
```

Install `attio` *or* `gtm-attio`, not both. They are the same code under two distribution names, and each installs the `attio` import package and the `attio` and `gtm-attio` commands. Releases before 0.28.3 install only `gtm-attio`.

Minimum Python: once a Python version reaches its [end of life](https://devguide.python.org/versions/), the SDK keeps supporting it for 3 more months and then raises the minimum.

### Scripts without a project

Use a [PEP 723](https://peps.python.org/pep-0723/) inline script, and `uv` installs the SDK on the fly:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["attio"]
# ///
import os

from attio import SDK

with SDK(oauth2=os.environ["ATTIO_API_KEY"]) as sdk:
    for obj in sdk.objects.get_v2_objects().data:
        print(obj.api_slug)
```

Run it with `uv run script.py`, or make it executable. A script without the metadata block runs with `uv run --with attio script.py`. For an interactive session, use `uvx --from attio python`.

<!-- Start Standalone CLI [cli] -->
## Standalone CLI

The `attio` command, also installed as `gtm-attio`, wraps the SDK in people, company and note commands. Each command identifies records by email, domain or ID, and prints one JSON envelope. You can run it without cloning or installing anything:

```bash
export ATTIO_API_KEY="your-attio-api-key"
uvx gtm-attio people upsert person@example.com \
  --first-name Ada --last-name Lovelace
```

### Running on demand with uvx

| Form | Use it when |
| --- | --- |
| `uvx gtm-attio …` | Always. This name works on every published version. |
| `uvx attio …` | You want the shorter name. Needs 0.28.3+; on older releases use `uvx --from attio gtm-attio …`. |
| `uvx gtm-attio@0.28.0 …` | You need reproducible runs pinned to one version. |
| `uvx gtm-attio@latest …` | You want a new release. Plain `uvx` reuses a version it already cached. |
| `uvx --from git+https://github.com/elviskahoro/sdk-python-attio gtm-attio …` | You need unreleased code from `main`. |
| `uv tool run gtm-attio …` | Only `uv` is on PATH. It's identical to `uvx`. |

Run `uvx gtm-attio <resource> <command> --help` for the full flag list of any command.

### Credentials

The CLI reads only `ATTIO_API_KEY`. It looks in the process environment first, then in `.env.local`, then in `.env` in the current directory. Without a key, the CLI returns the `missing_api_key` envelope. If Attio rejects the key (HTTP 401/403), the CLI returns `invalid_api_key`. The key needs record read/write scopes for `people` and `companies` commands, and note scopes for `notes`.

### Commands

| Command | Effect | Identity |
| --- | --- | --- |
| `people search EMAIL` | Read-only | Exact email |
| `people add EMAIL [flags]` | Creates a person; `duplicate_identity` if the email already exists | Email |
| `people update EMAIL [flags]` | Updates exactly one match; `record_not_found` or `multiple_matches` otherwise | Email |
| `people upsert EMAIL [flags]` | Creates a person, or updates the match | Email |
| `companies search --json PAYLOAD` | Read-only | Exact domain |
| `companies add --json PAYLOAD` | Creates a company; `duplicate_identity` if the domain already exists | Domain |
| `companies update --json PAYLOAD` | Updates exactly one match; `record_not_found` or `multiple_matches` otherwise | Domain |
| `notes list --json PAYLOAD` | Read-only | Parent record |
| `notes add --json PAYLOAD` | Creates a note on an existing record | Parent record |
| `notes update --json PAYLOAD` | Replaces only the fields you supply | Note ID |

### People

Every flag has a matching JSON key for `--json`:

| Flag | JSON key | Notes |
| --- | --- | --- |
| `EMAIL` (positional) | `email` | Identity key; required |
| `--add-email` (repeatable) | `additional_emails` (list) | Extra addresses to store |
| `--replace-emails` | `replace_emails` | `update`/`upsert` only: replace the stored emails with the identity email plus `--add-email` values |
| `--first-name`, `--last-name` | `first_name`, `last_name` | |
| `--job-title` | `job_title` | |
| `--phone` | `phone` | Start with `+` and the country code, or pair with `--phone-country-code` |
| `--phone-country-code` | `phone_country_code` | ISO-3166-1 alpha-2, e.g. `US` |
| `--linkedin` | `linkedin` | Profile URL or handle |
| `--location` | `location` | Needs `--country-code` |
| `--country-code` | `country_code` | ISO-3166-1 alpha-2 |
| `--location-mode city\|raw` | `location_mode` | How `--location` splits: `city` reads `locality, region` (the default); `raw` reads `street, locality, region` |
| `--company` | `company_domain` | Links the person to the company with this domain |
| `--notes` | `notes` | Writes the person's `notes` attribute |
| `--strict` | `strict` | Turns the cases below into errors |

`--json` replaces every flag, including the positional email, and rejects unknown keys.

Without `--strict`, the CLI keeps going in three cases, and reports each one in `warnings` and `skipped_fields`:

- **Invalid optional value** (a phone number, LinkedIn handle or domain): skipped.
- **Optional attribute your workspace doesn't have:** the write is retried without it.
- **`upsert` matches several people:** the CLI writes to the lexicographically smallest `record_id`, sets `partial_success`, and adds an `upsert_multi_match_selected_record` warning.

With `--strict`, these fail with `invalid_value`, `schema_mismatch` or `multiple_matches` instead. `update` and `add` never pick between duplicates.

```bash
uvx gtm-attio people search person@example.com
uvx gtm-attio people add person@example.com --first-name Ada --last-name Lovelace
uvx gtm-attio people update person@example.com --job-title Mathematician
uvx gtm-attio people upsert person@example.com --company example.com --strict
uvx gtm-attio people upsert --json '{"email":"person@example.com","first_name":"Ada","job_title":"Mathematician"}'
```

### Companies

`--json` is required and has the form `{"domain": "example.com", "values": {...}}`:

- `domain` is the identity. The CLI writes it to Attio's `domains` attribute, so it rejects `values.domains`.
- `values` uses the API's record format, `{"attribute_slug": [value, ...]}`. See [Record values](#record-values).
- `update` overwrites only the attributes you supply. Multi-select values are replaced, not appended.

```bash
uvx gtm-attio companies search --json '{"domain":"example.com"}'
uvx gtm-attio companies add --json '{"domain":"example.com","values":{"name":[{"value":"Example Inc"}]}}'
uvx gtm-attio companies update --json '{"domain":"example.com","values":{"description":["Prospect"]}}'
```

### Notes

| Command | JSON fields |
| --- | --- |
| `notes list` | `parent_object`, `parent_record_id`, and optionally `limit` (1-500, default 100) and `offset` (default 0) |
| `notes add` | `parent_object`, `parent_record_id`, `title`, `content`, and optionally `format` (`plaintext` by default, or `markdown`) |
| `notes update` | `note_id`, plus at least one of `title`, `content` and `format` |

`parent_object` is an object slug such as `people` or `companies`. `parent_record_id` is that record's ID, which you can read from the `record_id` of a people or company envelope.

```bash
uvx gtm-attio notes list --json '{"parent_object":"people","parent_record_id":"RECORD_ID"}'
uvx gtm-attio notes add --json '{"parent_object":"people","parent_record_id":"RECORD_ID","title":"Discovery call","content":"Discussed the launch plan.","format":"plaintext"}'
uvx gtm-attio notes update --json '{"note_id":"NOTE_ID","content":"Updated call notes."}'
```

### Output envelope

Every run that gets past argument parsing prints exactly one JSON object to stdout:

```json
{
  "success": true,
  "partial_success": false,
  "action": "created",
  "record_id": "bf071e1f-6035-429d-b874-d83ea64ea13b",
  "warnings": [],
  "skipped_fields": [],
  "errors": [],
  "meta": {
    "output_schema_version": "v1",
    "person": {
      "record_id": "bf071e1f-6035-429d-b874-d83ea64ea13b",
      "email_addresses": ["person@example.com"],
      "name": "Ada Lovelace",
      "created": true,
      "raw": {}
    }
  }
}
```

| Field | Contents |
| --- | --- |
| `action` | `created`, `updated`, `searched`, `listed` or `failed` |
| `record_id` | The ID of the person or company written (the note ID for notes); `null` for search, list and failures |
| `meta.results` | The matching records or notes from `search` or `list`. A people or company search returns at most 50, and adds a `search_result_limit_reached` warning when it hits that cap. |
| `meta.person`, `meta.company`, `meta.note` | The object that was written |
| `warnings[]` | Objects with `code`, `message`, `field` and `retryable` |
| `skipped_fields[]` | Objects with `field` and `reason` (`invalid_value` or `schema_mismatch`) |

A failure has the same shape, with `success: false` and the details in `errors`:

```json
{
  "success": false,
  "partial_success": false,
  "action": "failed",
  "record_id": null,
  "warnings": [],
  "skipped_fields": [],
  "errors": [
    {
      "code": "missing_api_key",
      "message": "ATTIO_API_KEY is not set. Export it or add it to .env.local or .env in the current directory.",
      "error_type": "CLIError",
      "fatal": true,
      "field": null,
      "status_code": null,
      "type": null,
      "details": {}
    }
  ],
  "meta": {"output_schema_version": "v1"}
}
```

| `errors[].code` | Meaning |
| --- | --- |
| `missing_api_key` | No `ATTIO_API_KEY` in the environment, `.env.local` or `.env` |
| `invalid_api_key` | Attio returned 401/403: a wrong key, or a missing scope |
| `invalid_json`, `validation_error` | `--json` isn't valid JSON, or a value failed validation; `message` names the field |
| `duplicate_identity` | `add` found an existing person or company with that email or domain |
| `record_not_found` | `update` matched nothing |
| `multiple_matches` | `update`, or `upsert --strict`, matched more than one record |
| `invalid_value`, `schema_mismatch` | With `--strict`: a value was invalid, or the workspace lacks the attribute |
| `uniqueness_conflict` | A person write included an email address that already belongs to another person |
| anything else | Attio's own error `code`, passed through with `status_code` and `details` from the API response |

Exit codes:

| Code | Meaning |
| --- | --- |
| `0` | Success, including `partial_success` |
| `1` | A failure, reported in a `success: false` envelope |
| `2` | A command-line usage error. argparse prints it to stderr and no JSON is emitted. |
<!-- End Standalone CLI [cli] -->

## Authentication

Every request needs an Attio access token, which you pass as `oauth2`. Despite the parameter name, it accepts either kind of [Attio access token](https://docs.attio.com/rest-api/guides/authentication):

- **API key:** a single-workspace token. Generate it in the developer settings of an app in your workspace.
- **OAuth 2.0 access token:** for an app installed in several workspaces.

```python
import os

from attio import SDK

with SDK(oauth2=os.environ["ATTIO_API_KEY"]) as sdk:
    print(sdk.meta.get_v2_self())  # which workspace and scopes the token has
```

Tokens carry scopes. Each method's reference page lists the scopes it needs under "Required scopes", and a 403 usually means one of them is missing.

## SDK Example Usage

```python
# Synchronous
import os

from attio import SDK

with SDK(oauth2=os.environ["ATTIO_API_KEY"]) as sdk:
    res = sdk.objects.get_v2_objects()
    for obj in res.data:
        print(obj.api_slug, obj.singular_noun)
```

Every method has an `_async` twin:

```python
# Asynchronous
import asyncio
import os

from attio import SDK


async def main() -> None:
    async with SDK(oauth2=os.environ["ATTIO_API_KEY"]) as sdk:
        res = await sdk.objects.get_v2_objects_async()
        print([obj.api_slug for obj in res.data])


asyncio.run(main())
```

### Finding the right method

Method names come mechanically from the HTTP verb and the path of the [Attio endpoint](https://docs.attio.com/rest-api/overview):

| Rule | Example |
| --- | --- |
| Name: `sdk.<resource>.<verb>_<path>`, where `/`, `{` and `}` become `_` | `POST /v2/objects/{object}/records/query` → `sdk.records.post_v2_objects_object_records_query` |
| A path that ends in a parameter gets a trailing `_` | `GET /v2/objects/{object}/records/{record_id}` → `sdk.records.get_v2_objects_object_records_record_id_` |
| Async: append `_async` and `await` the call | `await sdk.records.post_v2_objects_object_records_query_async(...)` |
| Arguments are keyword-only. Path params, query params and top-level body fields are all flattened into arguments; most write endpoints take one body argument, `data=` | `sdk.records.post_v2_objects_object_records(object="people", data={"values": {...}})` |
| Names that clash with Python builtins get a trailing `_` | `filter_=` on query methods; the `format_` key in a note body |
| A `{list}` path parameter is named `list_id` | `sdk.entries.post_v2_lists_list_entries_query(list_id="sales")` |
| Every method also accepts `retries=`, `timeout_ms=`, `server_url=` and `http_headers=` | See [Retries and timeouts](#retries-and-timeouts) |

Request bodies accept plain dicts (typed as `TypedDict`) or model instances from `attio.models`. Responses are Pydantic models with the payload under `.data`. `res.model_dump(mode="json", by_alias=True)` turns a response into plain JSON-compatible data.

The resource pages in [Available Resources and Operations](#available-resources-and-operations) document each method's parameters, an example, the response model and its errors. In a checkout, they live at `generated/docs/sdks/<resource>/README.md`, and the models at `generated/docs/models/`.

### Record values

Attio record attributes are written as `{attribute_slug: [value, ...]}`. The value is always a list, even for a single-value attribute. Common shapes (the CLI writes these):

| Attribute | Value |
| --- | --- |
| `email_addresses` (people) | `[{"email_address": "ada@example.com"}]` |
| `name` (people) | `[{"first_name": "Ada", "last_name": "Lovelace", "full_name": "Ada Lovelace"}]` |
| `job_title`, `description` (text) | `["Mathematician"]` |
| `phone_numbers` (people) | `[{"original_phone_number": "+14155550100"}]` |
| `domains` (companies) | `[{"domain": "example.com"}]` |
| `name` (companies) | `[{"value": "Example Inc"}]` |
| `associated_company` (person → company) | `[{"target_object": "companies", "domains": [{"domain": "example.com"}]}]` |

Attribute slugs and types differ between workspaces. List them with `sdk.attributes.get_v2_target_identifier_attributes(target="objects", identifier="people")`, and see Attio's [attribute types](https://docs.attio.com/rest-api/attribute-types/attribute-types) reference for every value shape.

## Common Workflows

### Query people, with a filter and pagination

```python
import os

from attio import SDK

PAGE = 100

with SDK(oauth2=os.environ["ATTIO_API_KEY"]) as sdk:
    offset = 0
    while True:
        page = sdk.records.post_v2_objects_object_records_query(
            object="people",
            filter_={"email_addresses": "ada@example.com"},
            limit=PAGE,
            offset=offset,
        )
        for record in page.data:
            print(record.id.record_id, record.values.get("name"))
        if len(page.data) < PAGE:
            break
        offset += PAGE
```

### Create a person

```python
import os

from attio import SDK

with SDK(oauth2=os.environ["ATTIO_API_KEY"]) as sdk:
    res = sdk.records.post_v2_objects_object_records(
        object="people",
        data={
            "values": {
                "email_addresses": [{"email_address": "ada@example.com"}],
                "name": [
                    {
                        "first_name": "Ada",
                        "last_name": "Lovelace",
                        "full_name": "Ada Lovelace",
                    },
                ],
                "job_title": ["Mathematician"],
            },
        },
    )
    print(res.data.id.record_id)
```

### Upsert a person by email

This creates the person, or updates the one record whose `matching_attribute` matches:

```python
import os

from attio import SDK

with SDK(oauth2=os.environ["ATTIO_API_KEY"]) as sdk:
    res = sdk.records.put_v2_objects_object_records(
        object="people",
        matching_attribute="email_addresses",
        data={
            "values": {
                "email_addresses": [{"email_address": "ada@example.com"}],
                "job_title": ["Mathematician"],
            },
        },
    )
    print(res.data.id.record_id)
```

### Add a note to a record

```python
import os

from attio import SDK

with SDK(oauth2=os.environ["ATTIO_API_KEY"]) as sdk:
    res = sdk.notes.post_v2_notes(
        data={
            "parent_object": "people",
            "parent_record_id": "bf071e1f-6035-429d-b874-d83ea64ea13b",
            "title": "Discovery call",
            "format_": "plaintext",
            "content": "Discussed the launch plan.",
        },
    )
    print(res.data.id.note_id)
```

### Fuzzy search across objects

```python
import os

from attio import SDK

with SDK(oauth2=os.environ["ATTIO_API_KEY"]) as sdk:
    res = sdk.records.post_v2_objects_records_search(
        query="ada",
        objects=["people", "companies"],
        request_as={"type": "workspace"},
        limit=10,
    )
    print(res.data)
```

Search is eventually consistent. When you need up-to-date results, use `post_v2_objects_object_records_query`.

## Available Resources and Operations

Each heading links to the resource's reference page and shows the attribute it lives on. Each method links to its section on that page.

### [Activities](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/activities/README.md): `sdk.activities`

* [get_v2_activities](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/activities/README.md#get_v2_activities) - List activities
* [post_v2_activities](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/activities/README.md#post_v2_activities) - Create an activity
* [get_v2_activities_activity_](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/activities/README.md#get_v2_activities_activity_) - Get an activity
* [patch_v2_activities_activity_](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/activities/README.md#patch_v2_activities_activity_) - Update an activity
* [delete_v2_activities_activity_](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/activities/README.md#delete_v2_activities_activity_) - Delete an activity

### [ActivityRecords](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/activityrecords/README.md): `sdk.activity_records`

* [post_v2_activities_activity_records_query](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/activityrecords/README.md#post_v2_activities_activity_records_query) - List activity records
* [post_v2_activities_activity_records](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/activityrecords/README.md#post_v2_activities_activity_records) - Create an activity record
* [put_v2_activities_activity_records](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/activityrecords/README.md#put_v2_activities_activity_records) - Upsert an activity record
* [get_v2_activities_activity_records_record_id_](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/activityrecords/README.md#get_v2_activities_activity_records_record_id_) - Get an activity record
* [patch_v2_activities_activity_records_record_id_](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/activityrecords/README.md#patch_v2_activities_activity_records_record_id_) - Update an activity record (append multiselect values)
* [put_v2_activities_activity_records_record_id_](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/activityrecords/README.md#put_v2_activities_activity_records_record_id_) - Update an activity record (overwrite multiselect values)
* [delete_v2_activities_activity_records_record_id_](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/activityrecords/README.md#delete_v2_activities_activity_records_record_id_) - Delete an activity record

### [Attributes](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/attributes/README.md): `sdk.attributes`

* [get_v2_target_identifier_attributes](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/attributes/README.md#get_v2_target_identifier_attributes) - List attributes
* [post_v2_target_identifier_attributes](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/attributes/README.md#post_v2_target_identifier_attributes) - Create an attribute
* [get_v2_target_identifier_attributes_attribute_](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/attributes/README.md#get_v2_target_identifier_attributes_attribute_) - Get an attribute
* [patch_v2_target_identifier_attributes_attribute_](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/attributes/README.md#patch_v2_target_identifier_attributes_attribute_) - Update an attribute
* [get_v2_target_identifier_attributes_attribute_options](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/attributes/README.md#get_v2_target_identifier_attributes_attribute_options) - List select options
* [post_v2_target_identifier_attributes_attribute_options](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/attributes/README.md#post_v2_target_identifier_attributes_attribute_options) - Create a select option
* [patch_v2_target_identifier_attributes_attribute_options_option_](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/attributes/README.md#patch_v2_target_identifier_attributes_attribute_options_option_) - Update a select option
* [get_v2_target_identifier_attributes_attribute_statuses](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/attributes/README.md#get_v2_target_identifier_attributes_attribute_statuses) - List statuses
* [post_v2_target_identifier_attributes_attribute_statuses](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/attributes/README.md#post_v2_target_identifier_attributes_attribute_statuses) - Create a status
* [patch_v2_target_identifier_attributes_attribute_statuses_status_](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/attributes/README.md#patch_v2_target_identifier_attributes_attribute_statuses_status_) - Update a status

### [CallRecordings](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/callrecordings/README.md): `sdk.call_recordings`

* [get_v2_meetings_meeting_id_call_recordings](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/callrecordings/README.md#get_v2_meetings_meeting_id_call_recordings) - List call recordings
* [post_v2_meetings_meeting_id_call_recordings](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/callrecordings/README.md#post_v2_meetings_meeting_id_call_recordings) - Create call recording
* [get_v2_meetings_meeting_id_call_recordings_call_recording_id_](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/callrecordings/README.md#get_v2_meetings_meeting_id_call_recordings_call_recording_id_) - Get call recording
* [delete_v2_meetings_meeting_id_call_recordings_call_recording_id_](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/callrecordings/README.md#delete_v2_meetings_meeting_id_call_recordings_call_recording_id_) - Delete call recording

### [Comments](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/comments/README.md): `sdk.comments`

* [post_v2_comments](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/comments/README.md#post_v2_comments) - Create a comment
* [get_v2_comments_comment_id_](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/comments/README.md#get_v2_comments_comment_id_) - Get a comment
* [delete_v2_comments_comment_id_](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/comments/README.md#delete_v2_comments_comment_id_) - Delete a comment

### [Emails](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/emails/README.md): `sdk.emails`

* [get_v2_emails](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/emails/README.md#get_v2_emails) - List emails

### [Entries](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/entries/README.md): `sdk.entries`

* [post_v2_lists_list_entries_query](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/entries/README.md#post_v2_lists_list_entries_query) - List entries
* [post_v2_lists_list_entries](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/entries/README.md#post_v2_lists_list_entries) - Create an entry (add record to list)
* [put_v2_lists_list_entries](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/entries/README.md#put_v2_lists_list_entries) - Upsert a list entry by parent
* [get_v2_lists_list_entries_entry_id_](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/entries/README.md#get_v2_lists_list_entries_entry_id_) - Get a list entry
* [patch_v2_lists_list_entries_entry_id_](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/entries/README.md#patch_v2_lists_list_entries_entry_id_) - Update a list entry (append multiselect values)
* [put_v2_lists_list_entries_entry_id_](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/entries/README.md#put_v2_lists_list_entries_entry_id_) - Update a list entry (overwrite multiselect values)
* [delete_v2_lists_list_entries_entry_id_](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/entries/README.md#delete_v2_lists_list_entries_entry_id_) - Delete a list entry
* [get_v2_lists_list_entries_entry_id_attributes_attribute_values](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/entries/README.md#get_v2_lists_list_entries_entry_id_attributes_attribute_values) - List attribute values for a list entry
* [put_v2_lists_list_entries_entry_id_attributes_attribute_values](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/entries/README.md#put_v2_lists_list_entries_entry_id_attributes_attribute_values) - Write list entry attribute values

### [Files](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/files/README.md): `sdk.files`

* [get_v2_files](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/files/README.md#get_v2_files) - List files
* [post_v2_files](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/files/README.md#post_v2_files) - Create a folder
* [post_v2_files_upload](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/files/README.md#post_v2_files_upload) - Upload a file
* [get_v2_files_file_id_](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/files/README.md#get_v2_files_file_id_) - Get a file
* [delete_v2_files_file_id_](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/files/README.md#delete_v2_files_file_id_) - Delete a file
* [get_v2_files_file_id_download](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/files/README.md#get_v2_files_file_id_download) - Download a file

### [Lists](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/lists/README.md): `sdk.lists`

* [get_v2_lists](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/lists/README.md#get_v2_lists) - List all lists
* [post_v2_lists](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/lists/README.md#post_v2_lists) - Create a list
* [get_v2_lists_list_](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/lists/README.md#get_v2_lists_list_) - Get a list
* [patch_v2_lists_list_](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/lists/README.md#patch_v2_lists_list_) - Update a list
* [get_v2_lists_list_views](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/lists/README.md#get_v2_lists_list_views) - List views for list

### [Meetings](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/meetings/README.md): `sdk.meetings`

* [get_v2_meetings](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/meetings/README.md#get_v2_meetings) - List meetings
* [post_v2_meetings](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/meetings/README.md#post_v2_meetings) - Create a meeting
* [get_v2_meetings_meeting_id_](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/meetings/README.md#get_v2_meetings_meeting_id_) - Get a meeting
* [patch_v2_meetings_meeting_id_](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/meetings/README.md#patch_v2_meetings_meeting_id_) - Update a meeting (append linked records)
* [put_v2_meetings_meeting_id_](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/meetings/README.md#put_v2_meetings_meeting_id_) - Update a meeting (overwrite linked records)
* [delete_v2_meetings_meeting_id_](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/meetings/README.md#delete_v2_meetings_meeting_id_) - Delete a meeting

### [Meta](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/meta/README.md): `sdk.meta`

* [get_v2_self](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/meta/README.md#get_v2_self) - Identify

### [Notes](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/notes/README.md): `sdk.notes`

* [get_v2_notes](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/notes/README.md#get_v2_notes) - List notes
* [post_v2_notes](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/notes/README.md#post_v2_notes) - Create a note
* [get_v2_notes_note_id_](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/notes/README.md#get_v2_notes_note_id_) - Get a note
* [patch_v2_notes_note_id_](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/notes/README.md#patch_v2_notes_note_id_) - Update a note
* [delete_v2_notes_note_id_](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/notes/README.md#delete_v2_notes_note_id_) - Delete a note

### [Objects](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/objects/README.md): `sdk.objects`

* [get_v2_objects](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/objects/README.md#get_v2_objects) - List objects
* [post_v2_objects](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/objects/README.md#post_v2_objects) - Create an object
* [get_v2_objects_object_](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/objects/README.md#get_v2_objects_object_) - Get an object
* [patch_v2_objects_object_](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/objects/README.md#patch_v2_objects_object_) - Update an object
* [delete_v2_objects_object_](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/objects/README.md#delete_v2_objects_object_) - Delete an object
* [get_v2_objects_object_views](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/objects/README.md#get_v2_objects_object_views) - List views for object

### [Records](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/records/README.md): `sdk.records`

* [post_v2_objects_object_records_query](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/records/README.md#post_v2_objects_object_records_query) - List records
* [post_v2_objects_object_records](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/records/README.md#post_v2_objects_object_records) - Create a record
* [put_v2_objects_object_records](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/records/README.md#put_v2_objects_object_records) - Upsert a record
* [get_v2_objects_object_records_record_id_](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/records/README.md#get_v2_objects_object_records_record_id_) - Get a record
* [patch_v2_objects_object_records_record_id_](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/records/README.md#patch_v2_objects_object_records_record_id_) - Update a record (append multiselect values)
* [put_v2_objects_object_records_record_id_](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/records/README.md#put_v2_objects_object_records_record_id_) - Update a record (overwrite multiselect values)
* [delete_v2_objects_object_records_record_id_](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/records/README.md#delete_v2_objects_object_records_record_id_) - Delete a record
* [post_v2_objects_object_records_merge](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/records/README.md#post_v2_objects_object_records_merge) - Merge two records
* [get_v2_objects_object_records_record_id_attributes_attribute_values](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/records/README.md#get_v2_objects_object_records_record_id_attributes_attribute_values) - List record attribute values
* [put_v2_objects_object_records_record_id_attributes_attribute_values](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/records/README.md#put_v2_objects_object_records_record_id_attributes_attribute_values) - Write record attribute values
* [get_v2_objects_object_records_record_id_entries](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/records/README.md#get_v2_objects_object_records_record_id_entries) - List record entries
* [post_v2_objects_records_search](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/records/README.md#post_v2_objects_records_search) - Search records

### [Sequences](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/sequences/README.md): `sdk.sequences`

* [post_v2_sequences_unsubscribed_emails](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/sequences/README.md#post_v2_sequences_unsubscribed_emails) - Add emails to the unsubscribe list

### [Sql](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/sql/README.md): `sdk.sql`

* [post_v2_sql](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/sql/README.md#post_v2_sql) - Query SQL

### [Tasks](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/tasks/README.md): `sdk.tasks`

* [get_v2_tasks](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/tasks/README.md#get_v2_tasks) - List tasks
* [post_v2_tasks](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/tasks/README.md#post_v2_tasks) - Create a task
* [get_v2_tasks_task_id_](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/tasks/README.md#get_v2_tasks_task_id_) - Get a task
* [patch_v2_tasks_task_id_](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/tasks/README.md#patch_v2_tasks_task_id_) - Update a task
* [delete_v2_tasks_task_id_](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/tasks/README.md#delete_v2_tasks_task_id_) - Delete a task

### [Threads](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/threads/README.md): `sdk.threads`

* [get_v2_threads](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/threads/README.md#get_v2_threads) - List threads
* [get_v2_threads_thread_id_](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/threads/README.md#get_v2_threads_thread_id_) - Get a thread and its comments

### [Transcripts](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/transcripts/README.md): `sdk.transcripts`

* [get_v2_meetings_meeting_id_call_recordings_call_recording_id_transcript](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/transcripts/README.md#get_v2_meetings_meeting_id_call_recordings_call_recording_id_transcript) - Deprecated: Get call transcript

### [Webhooks](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/webhooks/README.md): `sdk.webhooks`

* [get_v2_webhooks](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/webhooks/README.md#get_v2_webhooks) - List webhooks
* [post_v2_webhooks](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/webhooks/README.md#post_v2_webhooks) - Create a webhook
* [get_v2_webhooks_webhook_id_](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/webhooks/README.md#get_v2_webhooks_webhook_id_) - Get a webhook
* [patch_v2_webhooks_webhook_id_](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/webhooks/README.md#patch_v2_webhooks_webhook_id_) - Update a webhook
* [delete_v2_webhooks_webhook_id_](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/webhooks/README.md#delete_v2_webhooks_webhook_id_) - Delete a webhook

### [WorkspaceMembers](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/workspacemembers/README.md): `sdk.workspace_members`

* [get_v2_workspace_members](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/workspacemembers/README.md#get_v2_workspace_members) - List workspace members
* [get_v2_workspace_members_workspace_member_id_](https://github.com/elviskahoro/sdk-python-attio/blob/main/generated/docs/sdks/workspacemembers/README.md#get_v2_workspace_members_workspace_member_id_) - Get a workspace member

## File uploads

Pass a file as a stream rather than reading it into memory; `bytes` also work:

```python
import os

from attio import SDK

with SDK(oauth2=os.environ["ATTIO_API_KEY"]) as sdk, open("example.pdf", "rb") as content:
    res = sdk.files.post_v2_files_upload(
        file={"file_name": "example.pdf", "content": content},
        object="people",
        record_id="bf071e1f-6035-429d-b874-d83ea64ea13b",
    )
    print(res.data)
```

## Retries and timeouts

By default, a failed request is not retried. Pass a `RetryConfig`, either per call with `retries=` or for the whole client with `retry_config=`. A retry happens on HTTP 429, 500, 502, 503 and 504, and also on connection errors when `retry_connection_errors` is set:

```python
import os

from attio import SDK
from attio.utils import BackoffStrategy, RetryConfig

retry = RetryConfig(
    "backoff",
    BackoffStrategy(
        initial_interval=500,  # ms before the first retry
        max_interval=60_000,  # ms cap on a single wait
        exponent=1.5,  # growth factor between waits
        max_elapsed_time=300_000,  # ms before giving up
    ),
    retry_connection_errors=True,
)

# For every method on this client:
with SDK(oauth2=os.environ["ATTIO_API_KEY"], retry_config=retry, timeout_ms=30_000) as sdk:
    # Or per call; this overrides the client-wide setting:
    res = sdk.objects.get_v2_objects(retries=retry, timeout_ms=10_000)
```

`timeout_ms` is in milliseconds. Set it on `SDK(...)` for every request, or on a single call.

## Error Handling

```python
import os

import httpx
from attio import SDK, errors

with SDK(oauth2=os.environ["ATTIO_API_KEY"]) as sdk:
    try:
        sdk.records.get_v2_objects_object_records_record_id_(
            object="people",
            record_id="00000000-0000-0000-0000-000000000000",
        )
    except errors.SDKError as e:
        print(e.status_code)  # e.g. 404
        print(e.message)
        print(e.body)  # Attio's JSON error body: status_code, type, code, message
    except httpx.RequestError as e:
        print("network error:", e)
```

| Exception | When |
| --- | --- |
| `errors.SDKError` | Base class for every HTTP error response. Has `status_code`, `message`, `body`, `headers` and `raw_response`. |
| `errors.<Verb><Path><Kind>Error` | A typed subclass for each documented Attio error, e.g. `PostV2ObjectsObjectRecordsBadRequestInvalidRequestError` (400 on create record) or `GetV2NotesNoteIDNotFoundError`. Has the parsed body in `e.data` (`status_code`, `type`, `code`, `message`). |
| `errors.SDKDefaultError` | Any other 4XX or 5XX response. |
| `errors.ResponseValidationError` | The response didn't match the SDK's model. The Pydantic error is in `e.cause`. |
| `httpx.RequestError` (`ConnectError`, `TimeoutException`) | Network failure. Not an `SDKError`. |

The typed classes are long and specific to one endpoint. Catch `errors.SDKError` and branch on `e.status_code` (404, 409, 429, …), or on `e.data.code` when the class has one. Each method's reference page lists its error classes under "Errors", and the classes themselves live in [`generated/src/attio/errors/`](https://github.com/elviskahoro/sdk-python-attio/tree/main/generated/src/attio/errors).

## Server Selection

The default server is `https://api.attio.com`. To override it, pass `server_url` to `SDK(...)`, or to a single call:

```python
import os

from attio import SDK

sdk = SDK(oauth2=os.environ["ATTIO_API_KEY"], server_url="https://api.attio.com")
```

## Custom HTTP Client

The SDK uses [httpx](https://www.python-httpx.org/). For proxies, custom headers, transport timeouts or event hooks, pass your own client: `client=` for sync calls, `async_client=` for async ones:

```python
import os

import httpx
from attio import SDK

sdk = SDK(
    oauth2=os.environ["ATTIO_API_KEY"],
    client=httpx.Client(headers={"x-custom-header": "someValue"}),
    async_client=httpx.AsyncClient(headers={"x-custom-header": "someValue"}),
)
```

Any object that implements the `attio.httpclient.HttpClient` or `AsyncHttpClient` protocol (`send` and `build_request`) also works, for example a wrapper that adds logging.

To run on [httpx2](https://httpx2.pydantic.dev/), Pydantic's fork of httpx, alias it before importing the SDK:

```python
import httpx2

httpx2.alias_httpx()

from attio import SDK  # noqa: E402
```

## Resource Management

`SDK` is a context manager. On exit it closes the HTTP clients it created; a finalizer closes them otherwise. In a long-running program, create one client and reuse it:

```python
import os

from attio import SDK


def main() -> None:
    with SDK(oauth2=os.environ["ATTIO_API_KEY"]) as sdk:
        ...  # reuse sdk for every call


async def amain() -> None:
    async with SDK(oauth2=os.environ["ATTIO_API_KEY"]) as sdk:
        ...  # reuse sdk for every call
```

## Debugging

```python
import logging
import os

from attio import SDK

logging.basicConfig(level=logging.DEBUG)
sdk = SDK(oauth2=os.environ["ATTIO_API_KEY"], debug_logger=logging.getLogger("attio"))
```

The debug logger records each request's method, URL, **headers** and body, and each response. The headers include `Authorization: Bearer <your key>`, so never share these logs or commit them.

## Troubleshooting

### 401 or 403 responses

- From the CLI, this is the `invalid_api_key` error. From the SDK, it's an `SDKError` with status 401 or 403.
- Check that the key is current and has the scopes on the method's reference page. Record writes, for example, need `record_permission:read-write`.

### 400 validation errors on create or update

- Values must be lists in the shapes shown in [Record values](#record-values), and every attribute slug must exist in your workspace.
- Start from one attribute and add the rest one at a time. The error's `message` names the attribute it rejected.

### `uvx` runs an old version

`uvx` reuses a cached environment. Run `uvx gtm-attio@latest …`, pin a version with `@X.Y.Z`, or add `--refresh`.

### `uvx attio`: "An executable named `attio` is not provided by package `attio`"

The resolved release predates 0.28.3, so it ships only `gtm-attio`. Run `uvx gtm-attio …`, `uvx attio@latest …` or `uvx --from attio gtm-attio …`.

### `uvx: command not found`

`uvx` ships with [uv](https://docs.astral.sh/uv/getting-started/installation/). `uv tool run …` does the same thing.

### Async usage issues

- Inside `async with SDK(...)`, use the `_async` methods. The sync methods block the event loop.
- Don't mix sync and async clients in the same call path.

## Maintaining this repository

This README is maintained by hand. Speakeasy generates everything under `generated/`: the SDK source, `generated/docs/` and `generated/USAGE.md`. `ci/post_generate_patch.py` owns the [Standalone CLI](#standalone-cli) section and the `[project.scripts]` entry points, and re-applies them after every regeneration. [AGENTS.md](https://github.com/elviskahoro/sdk-python-attio/blob/main/AGENTS.md) covers regeneration, the overlay and releases.
