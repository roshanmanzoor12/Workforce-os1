from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


SavedScopeType = Literal["department", "team"]


class ScopeGrantCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scope_type: SavedScopeType
    resource_id: uuid.UUID


class ScopeGrantPublic(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )

    membership_id: uuid.UUID
    scope_type: SavedScopeType
    resource_id: uuid.UUID
    granted_by_user_id: uuid.UUID
    created_at: datetime


class ScopeGrantListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    membership_id: uuid.UUID
    grants: list[ScopeGrantPublic]


class ScopeGrantDeleteResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    membership_id: uuid.UUID
    scope_type: SavedScopeType
    resource_id: uuid.UUID
    removed: bool


__all__ = [
    "SavedScopeType",
    "ScopeGrantCreateRequest",
    "ScopeGrantPublic",
    "ScopeGrantListResponse",
    "ScopeGrantDeleteResponse",
]