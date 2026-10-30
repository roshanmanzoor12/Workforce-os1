from __future__ import annotations

import uuid

from fastapi import (
    APIRouter,
    status,
)

from app.db.tenant_dependency import (
    TenantScope,
)
from app.modules.meetings.router import (
    actor_user_id_from_scope,
)
from app.modules.meetings.self_schemas import (
    MeetingInvitationListResponse,
    MeetingSelfResponse,
    MeetingSelfResponseRequest,
)
from app.modules.meetings.self_service import (
    MeetingSelfService,
)
from app.modules.workspace_permissions.permissions import (
    WorkspacePermission,
)
from app.modules.workspace_permissions.service import (
    WorkspacePermissionService,
)


router = APIRouter(
    prefix=(
        "/workspaces/{workspace_id}/"
        "meetings/me"
    ),
    tags=["Meetings"],
)


def self_service(
    scope: TenantScope,
) -> MeetingSelfService:
    return MeetingSelfService(
        scope.session
    )


def permission_service(
    scope: TenantScope,
) -> WorkspacePermissionService:
    return WorkspacePermissionService(
        scope
    )


@router.get(
    "/invitations",
    response_model=(
        MeetingInvitationListResponse
    ),
    status_code=status.HTTP_200_OK,
    summary="List my meeting invitations",
)
async def list_my_meeting_invitations(
    scope: TenantScope,
) -> MeetingInvitationListResponse:
    permission_service(
        scope
    ).require(
        WorkspacePermission
        .MEETINGS_VIEW
        .value
    )

    return await self_service(
        scope
    ).list_my_invitations(
        actor_user_id=(
            actor_user_id_from_scope(
                scope
            )
        )
    )


@router.patch(
    "/{meeting_id}/response",
    response_model=MeetingSelfResponse,
    status_code=status.HTTP_200_OK,
    summary=(
        "Accept or decline my meeting invitation"
    ),
)
async def respond_to_my_meeting_invitation(
    meeting_id: uuid.UUID,
    payload: MeetingSelfResponseRequest,
    scope: TenantScope,
) -> MeetingSelfResponse:
    permission_service(
        scope
    ).require(
        WorkspacePermission
        .MEETINGS_VIEW
        .value
    )

    return await self_service(
        scope
    ).respond_to_invitation(
        actor_user_id=(
            actor_user_id_from_scope(
                scope
            )
        ),
        meeting_id=meeting_id,
        request=payload,
    )


__all__ = [
    "router",
]