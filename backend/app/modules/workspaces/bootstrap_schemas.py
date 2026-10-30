from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class WorkspaceBootstrapResponse(BaseModel):
    # Fields required by apps/web/types/workspace-access.ts
    workspace_id: str
    membership_id: str
    role_key: str
    permissions: list[str] = Field(default_factory=list)
    moderation: dict[str, bool] = Field(default_factory=dict)
    available_roles: list[dict[str, Any]] = Field(default_factory=list)
    # Preserve older clients' bootstrap fields.
    workspace: dict[str, Any] = Field(default_factory=dict)
    membership: dict[str, Any] = Field(default_factory=dict)
    roles: list[str] = Field(default_factory=list)
    scopes: list[str] = Field(default_factory=list)
    entitlements: dict[str, Any] = Field(default_factory=dict)
    navigation: list[str] = Field(default_factory=list)
    setup_status: dict[str, Any] = Field(default_factory=dict)


__all__ = ["WorkspaceBootstrapResponse"]
