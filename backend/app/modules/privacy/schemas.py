from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PrivacyPolicyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=500)


class PrivacyPolicyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None


class PrivacyPolicyPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    name: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class PrivacyZoneCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    zone_type: str = Field(
        ...,
        pattern=r"^(location|schedule|device|network)$",
    )
    value: str = Field(..., min_length=1, max_length=500)


class PrivacyZoneUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    value: str | None = Field(default=None, min_length=1, max_length=500)
    is_active: bool | None = None


class PrivacyZonePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    name: str
    zone_type: str
    value: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class PrivacyExclusionCreate(BaseModel):
    exclusion_type: str = Field(
        ...,
        pattern=r"^(ip|device|cookie|session|user_agent)$",
    )
    value: str = Field(..., min_length=1, max_length=500)
    reason: str | None = Field(default=None, max_length=500)


class PrivacyExclusionUpdate(BaseModel):
    value: str | None = Field(default=None, min_length=1, max_length=500)
    reason: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None


class PrivacyExclusionPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    exclusion_type: str
    value: str
    reason: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime