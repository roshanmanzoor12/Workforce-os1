from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator


class OrganizationSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True,
    )


class OrganizationUpdateRequest(OrganizationSchema):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )

    timezone: str | None = Field(
        default=None,
        min_length=1,
        max_length=64,
    )

    logo_url: str | None = Field(
        default=None,
        max_length=2048,
    )

    @field_validator("name", "timezone")
    @classmethod
    def normalize_text(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = value.strip()

        if not normalized:
            raise ValueError("Value cannot be blank.")

        return normalized

    @field_validator("logo_url")
    @classmethod
    def normalize_logo_url(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = value.strip()

        if not normalized:
            return None

        return normalized


class OrganizationResponse(OrganizationSchema):
    id: uuid.UUID
    name: str
    slug: str
    timezone: str
    logo_url: str | None
    status: str
    is_active: bool
    created_by_user_id: uuid.UUID


class OrganizationWorkspaceResponse(OrganizationSchema):
    id: uuid.UUID
    name: str
    slug: str
    timezone: str
    logo_url: str | None
    status: str
    is_active: bool


__all__ = [
    "OrganizationSchema",
    "OrganizationUpdateRequest",
    "OrganizationResponse",
    "OrganizationWorkspaceResponse",
]