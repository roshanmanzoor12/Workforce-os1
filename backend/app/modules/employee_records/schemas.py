from __future__ import annotations

import uuid
from datetime import date
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


EmployeeRecordType = Literal[
    "personal",
    "contact",
    "emergency_contact",
    "employment",
    "education",
    "certification",
    "document",
    "other",
]


class EmployeeRecordSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )


class EmployeeRecordCreateRequest(
    EmployeeRecordSchema
):
    record_type: EmployeeRecordType

    title: str = Field(
        min_length=1,
        max_length=150,
    )

    value: str | None = None

    effective_date: date | None = None

    notes: str | None = None

    metadata_json: dict | None = None

    @field_validator(
        "title",
        "value",
        "notes",
        mode="before",
    )
    @classmethod
    def normalize_strings(
        cls,
        value,
    ):
        if value is None:
            return None

        if not isinstance(value, str):
            return value

        value = value.strip()
        return value or None


class EmployeeRecordUpdateRequest(
    EmployeeRecordSchema
):
    record_type: EmployeeRecordType | None = None

    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=150,
    )

    value: str | None = None

    effective_date: date | None = None

    notes: str | None = None

    metadata_json: dict | None = None

    @field_validator(
        "title",
        "value",
        "notes",
        mode="before",
    )
    @classmethod
    def normalize_strings(
        cls,
        value,
    ):
        if value is None:
            return None

        if not isinstance(value, str):
            return value

        value = value.strip()
        return value or None


class EmployeeRecordResponse(
    EmployeeRecordSchema
):
    id: uuid.UUID
    employee_id: uuid.UUID
    record_type: EmployeeRecordType
    title: str
    value: str | None
    effective_date: date | None
    notes: str | None
    metadata_json: dict | None


class EmployeeRecordListResponse(
    EmployeeRecordSchema
):
    items: list[EmployeeRecordResponse] = Field(
        default_factory=list,
    )

    total: int = Field(
        ge=0,
    )


class EmployeeRecordDeleteResponse(
    EmployeeRecordSchema
):
    success: bool
    message: str


__all__ = [
    "EmployeeRecordType",
    "EmployeeRecordCreateRequest",
    "EmployeeRecordUpdateRequest",
    "EmployeeRecordResponse",
    "EmployeeRecordListResponse",
    "EmployeeRecordDeleteResponse",
]