"""Shared lightweight Attio CLI test doubles."""

from __future__ import annotations

from types import SimpleNamespace as NS
from typing import Any


def record(
    record_id: str,
    emails: list[str] | None = None,
    name: str | None = None,
    *,
    email: str | None = None,
) -> Any:
    if email is not None:
        emails = [email]
    values = {
        "email_addresses": [NS(email_address=value) for value in emails or []],
        "name": [],
    }
    if name:
        first_name, _, last_name = name.partition(" ")
        values["name"] = [
            NS(first_name=first_name, last_name=last_name, full_name=name)
        ]
    return NS(id=NS(record_id=record_id), values=values)


class FakeRecords:
    def __init__(self, matches=None, existing=None, written=None):
        self.matches = matches or []
        self.existing = existing or record("existing")
        self.written = written or record("written")
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


class FakeNotes:
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


class FakeClient:
    def __init__(self, records=None, notes=None):
        self.records = records if records is not None else FakeRecords()
        self.notes = notes if notes is not None else FakeNotes()
