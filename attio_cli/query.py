"""Validated CLI input models."""

from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class PersonUpsertQuery(BaseModel):
    """Input accepted by ``people upsert`` and its JSON payload form."""

    model_config = ConfigDict(extra="forbid")

    email: str
    additional_emails: list[str] = Field(default_factory=list)
    replace_emails: bool = False
    first_name: str | None = None
    last_name: str | None = None
    job_title: str | None = None
    phone: str | None = None
    phone_country_code: str | None = None
    linkedin: str | None = None
    location: str | None = None
    country_code: str | None = None
    company_domain: str | None = None
    notes: str | None = None
    strict: bool = False
    location_mode: Literal["city", "raw"] = "city"

    @field_validator("email")
    @classmethod
    def strip_email(cls, value: str) -> str:
        return value.strip()

    @model_validator(mode="after")
    def validate_composite_location(self) -> PersonUpsertQuery:
        if self.location and not self.country_code:
            raise ValueError(
                "--country-code is required with --location so Attio receives "
                "the complete primary_location value. Use an ISO-3166-1 "
                "alpha-2 code such as US or GB."
            )
        if self.country_code is not None and not re.fullmatch(
            r"[A-Za-z]{2}", self.country_code
        ):
            raise ValueError("country_code must be a two-letter ISO-3166-1 alpha-2 code")
        if self.phone_country_code is not None and not re.fullmatch(
            r"[A-Za-z]{2}", self.phone_country_code
        ):
            raise ValueError(
                "phone_country_code must be a two-letter ISO-3166-1 alpha-2 code"
            )
        if not self.email:
            raise ValueError("email must not be empty")
        return self


class CompanyPayload(BaseModel):
    """Validated input for exact-domain company commands."""

    model_config = ConfigDict(extra="forbid")

    domain: str
    values: dict[str, list[Any]] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_domain(self) -> CompanyPayload:
        if not self.domain.strip() or "." not in self.domain.strip():
            raise ValueError("domain must be a fully qualified company domain")
        if "domains" in self.values:
            raise ValueError(
                "values.domains is reserved for the domain identity field"
            )
        return self


class NoteListPayload(BaseModel):
    """Validated input for listing notes on one record."""

    model_config = ConfigDict(extra="forbid")

    parent_object: str = Field(min_length=1)
    parent_record_id: str = Field(min_length=1)
    limit: int = Field(default=100, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


class NoteAddPayload(BaseModel):
    """Validated input for creating a note."""

    model_config = ConfigDict(extra="forbid")

    parent_object: str = Field(min_length=1)
    parent_record_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    content: str = Field(min_length=1)
    format: Literal["plaintext", "markdown"] = "plaintext"


class NoteUpdatePayload(BaseModel):
    """Validated input for updating a note."""

    model_config = ConfigDict(extra="forbid")

    note_id: str = Field(min_length=1)
    title: str | None = None
    content: str | None = None
    format: Literal["plaintext", "markdown"] | None = None

    @model_validator(mode="after")
    def require_update_fields(self) -> NoteUpdatePayload:
        if self.title is None and self.content is None and self.format is None:
            raise ValueError("at least one of title, content, or format is required")
        return self
