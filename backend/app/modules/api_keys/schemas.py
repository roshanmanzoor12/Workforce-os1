from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SecretStr,
    field_validator,
)


class APIKeyCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    name: str = Field(min_length=1, max_length=120)
    scopes: list[str] = Field(min_length=1, max_length=50)
    expires_at: datetime | None = None

    @field_validator("scopes")
    @classmethod
    def normalize_scopes(cls, value: list[str]) -> list[str]:
        normalized = sorted({item.strip() for item in value})

        if not normalized or any(not item for item in normalized):
            raise ValueError("Scopes must contain non-empty values.")

        return normalized

    @field_validator("expires_at")
    @classmethod
    def validate_expiry(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None

        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Expiry must include a timezone.")

        value = value.astimezone(timezone.utc)

        if value <= datetime.now(timezone.utc):
            raise ValueError("Expiry must be in the future.")

        return value


class APIKeyPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    created_by_user_id: UUID
    name: str
    key_prefix: str
    scopes: list[str]
    expires_at: datetime | None
    revoked_at: datetime | None
    revoked_by_user_id: UUID | None
    last_used_at: datetime | None
    created_at: datetime
    updated_at: datetime


class APIKeyIssued(BaseModel):
    key: APIKeyPublic
    secret: SecretStr

    # SecretStr masks repr/logging. The HTTP router explicitly returns
    # the raw value only for the create and rotate responses.