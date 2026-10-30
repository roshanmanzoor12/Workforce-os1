from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    field_validator,
)

from app.modules.notes.personal_document import (
    validate_personal_content,
)


PersonalNoteFilter = Literal[
    "all",
    "pinned",
    "checklists",
    "archived",
]

PersonalNoteSort = Literal[
    "updated",
    "created",
    "oldest",
    "title",
]


class PersonalNoteSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True,
    )


class PersonalNoteCreateRequest(PersonalNoteSchema):
    title: str = Field(
        min_length=1,
        max_length=200,
    )

    content: str = Field(
        default="",
        max_length=100000,
    )

    @field_validator("title", mode="before")
    @classmethod
    def validate_title(cls, value: object) -> object:
        if isinstance(value, str):
            value = value.strip()

            if not value:
                raise ValueError(
                    "Note title cannot be blank."
                )

        return value

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        return validate_personal_content(value)


class PersonalNoteUpdateRequest(PersonalNoteSchema):
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

    @field_validator("content")
    @classmethod
    def validate_content(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return value

        return validate_personal_content(value)


class PersonalNotePublic(PersonalNoteSchema):
    id: uuid.UUID
    owner_user_id: uuid.UUID

    title: str
    content: str

    is_pinned: bool
    is_archived: bool

    created_at: datetime
    updated_at: datetime

    # Derived from content; no additional database columns.
    content_format: Literal["plain", "rich"] = "plain"
    plain_text: str = ""
    tags: list[str] = Field(default_factory=list)

    checklist_total: int = Field(
        default=0,
        ge=0,
    )

    checklist_completed: int = Field(
        default=0,
        ge=0,
    )


class PersonalNoteListResponse(PersonalNoteSchema):
    items: list[PersonalNotePublic]
    total: int = Field(ge=0)


class PersonalNoteStatsResponse(PersonalNoteSchema):
    total: int = Field(ge=0)
    pinned: int = Field(ge=0)
    archived: int = Field(ge=0)


__all__ = [
    "PersonalNoteFilter",
    "PersonalNoteSort",
    "PersonalNoteCreateRequest",
    "PersonalNoteUpdateRequest",
    "PersonalNotePublic",
    "PersonalNoteListResponse",
    "PersonalNoteStatsResponse",
]