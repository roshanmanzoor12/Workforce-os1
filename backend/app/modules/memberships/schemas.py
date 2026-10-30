from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from app.modules.memberships.enums import (
    WorkspaceMembershipRole,
    WorkspaceMembershipStatus,
)


class WorkspaceMembershipCreateRequest(
    BaseModel,
):
    user_id: uuid.UUID | None = None

    role: WorkspaceMembershipRole = (
        WorkspaceMembershipRole.MEMBER
    )


class WorkspaceMembershipRoleRequest(
    BaseModel,
):
    role: WorkspaceMembershipRole


class WorkspaceMembershipRoleUpdateRequest(
    BaseModel,
):
    role: WorkspaceMembershipRole


class WorkspaceMembershipStatusUpdateRequest(
    BaseModel,
):
    status: WorkspaceMembershipStatus


class WorkspaceMembershipResponse(
    BaseModel,
):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: uuid.UUID

    workspace_id: uuid.UUID
    user_id: uuid.UUID

    role_key: WorkspaceMembershipRole
    status: WorkspaceMembershipStatus

    invited_by_user_id: (
        uuid.UUID | None
    )

    invited_at: datetime | None
    joined_at: datetime | None
    suspended_at: datetime | None
    removed_at: datetime | None

    created_at: datetime
    updated_at: datetime


class WorkspaceMembershipListResponse(
    BaseModel,
):
    workspace_id: uuid.UUID

    items: list[
        WorkspaceMembershipResponse
    ] = Field(
        default_factory=list,
    )


class WorkspaceMembershipAccessResponse(
    BaseModel,
):
    workspace_id: uuid.UUID
    user_id: uuid.UUID

    is_member: bool

    role: (
        WorkspaceMembershipRole
        | None
    ) = None

    status: (
        WorkspaceMembershipStatus
        | None
    ) = None

    can_manage_members: bool = False


__all__ = [
    "WorkspaceMembershipCreateRequest",
    "WorkspaceMembershipRoleRequest",
    "WorkspaceMembershipRoleUpdateRequest",
    "WorkspaceMembershipStatusUpdateRequest",
    "WorkspaceMembershipResponse",
    "WorkspaceMembershipListResponse",
    "WorkspaceMembershipAccessResponse",
]