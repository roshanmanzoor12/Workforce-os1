from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    field_validator,
)


class NoteSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True,
    )


class NoteCreateRequest(NoteSchema):
    owner_employee_id: uuid.UUID

    title: str = Field(
        min_length=1,
        max_length=200,
    )

    content: str = Field(
        default="",
        max_length=100000,
    )

    @field_validator(
        "title",
        mode="before",
    )
    @classmethod
    def validate_title(
        cls,
        value: object,
    ) -> object:
        if isinstance(value, str):
            value = value.strip()

            if not value:
                raise ValueError(
                    "Note title cannot be blank."
                )

        return value


class NoteUpdateRequest(NoteSchema):
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )

    content: str | None = Field(
        default=None,
        max_length=100000,
    )

    is_pinned: bool | None = None
    is_archived: bool | None = None

    @field_validator(
        "title",
        "content",
        "is_pinned",
        "is_archived",
        mode="before",
    )
    @classmethod
    def validate_supplied_update(
        cls,
        value: object,
        info: ValidationInfo,
    ) -> object:
        """
        Omitted fields retain their default values and are
        excluded by model_dump(exclude_unset=True).

        Explicit null values are rejected because the
        corresponding database columns are not nullable.
        """
        if value is None:
            raise ValueError(
                f"{info.field_name} cannot be null. "
                "Omit the field to leave it unchanged."
            )

        if (
            info.field_name == "title"
            and isinstance(value, str)
        ):
            value = value.strip()

            if not value:
                raise ValueError(
                    "Note title cannot be blank."
                )

        return value


class NotePublic(NoteSchema):
    id: uuid.UUID
    owner_employee_id: uuid.UUID

    title: str
    content: str

    is_pinned: bool
    is_archived: bool

    created_at: datetime
    updated_at: datetime


class NoteListResponse(NoteSchema):
    items: list[NotePublic]

    total: int = Field(
        ge=0,
    )


__all__ = [
    "NoteCreateRequest",
    "NoteUpdateRequest",
    "NotePublic",
    "NoteListResponse",
]