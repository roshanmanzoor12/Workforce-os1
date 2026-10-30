from __future__ import annotations

import uuid

from fastapi import (
    APIRouter,
    Query,
    Response,
    status,
)

from app.db.tenant_dependency import (
    TenantScope,
)
from app.modules.meetings.enums import (
    MeetingStatus,
)
from app.modules.meetings.schemas import (
    MeetingCreateRequest,
    MeetingDetailResponse,
    MeetingListResponse,
    MeetingParticipantAddRequest,
    MeetingParticipantResponse,
    MeetingParticipantStatusRequest,
    MeetingResponse,
    MeetingUpdateRequest,
)
from app.modules.meetings.service import (
    MeetingService,
)
from app.modules.workspace_permissions.permissions import (
    WorkspacePermission,
)
from app.modules.workspace_permissions.service import (
    WorkspacePermissionService,
)


router = APIRouter(
    prefix=(
        "/workspaces/{workspace_id}/meetings"
    ),
    tags=["Meetings"],
)


def permission_service(
    scope: TenantScope,
) -> WorkspacePermissionService:
    return WorkspacePermissionService(
        scope
    )


def meeting_service(
    scope: TenantScope,
) -> MeetingService:
    return MeetingService(
        scope.session
    )


def actor_user_id_from_scope(
    scope: TenantScope,
) -> uuid.UUID:
    value = getattr(
        scope,
        "actor_user_id",
        None,
    )

    if value is None:
        context = getattr(
            scope,
            "context",
            None,
        )

        if context is not None:
            value = getattr(
                context,
                "actor_user_id",
                None,
            )

    if value is None:
        user = getattr(
            scope,
            "user",
            None,
        )

        if user is not None:
            value = getattr(
                user,
                "id",
                None,
            )

    if value is None:
        raise RuntimeError(
            "TenantScope does not expose "
            "authenticated user id."
        )

    if isinstance(
        value,
        uuid.UUID,
    ):
        return value

    return uuid.UUID(
        str(value)
    )


@router.post(
    "",
    response_model=MeetingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create meeting",
)
async def create_meeting(
    payload: MeetingCreateRequest,
    scope: TenantScope,
) -> MeetingResponse:
    permission_service(
        scope
    ).require(
        WorkspacePermission
        .MEETINGS_CREATE
        .value
    )

    return await meeting_service(
        scope
    ).create_meeting(
        actor_user_id=(
            actor_user_id_from_scope(
                scope
            )
        ),
        request=payload,
    )


@router.get(
    "",
    response_model=MeetingListResponse,
    summary="List meetings",
)
async def list_meetings(
    scope: TenantScope,
    meeting_status: (
        MeetingStatus | None
    ) = Query(
        default=None,
        alias="status",
    ),
) -> MeetingListResponse:
    permission_service(
        scope
    ).require(
        WorkspacePermission
        .MEETINGS_VIEW
        .value
    )

    return await meeting_service(
        scope
    ).list_meetings(
        status=meeting_status
    )


@router.get(
    "/{meeting_id}",
    response_model=MeetingDetailResponse,
    summary="Get meeting",
)
async def get_meeting(
    meeting_id: uuid.UUID,
    scope: TenantScope,
) -> MeetingDetailResponse:
    permission_service(
        scope
    ).require(
        WorkspacePermission
        .MEETINGS_VIEW
        .value
    )

    return await meeting_service(
        scope
    ).get_meeting(
        meeting_id=meeting_id
    )


@router.patch(
    "/{meeting_id}",
    response_model=MeetingResponse,
    summary="Update meeting",
)
async def update_meeting(
    meeting_id: uuid.UUID,
    payload: MeetingUpdateRequest,
    scope: TenantScope,
) -> MeetingResponse:
    permission_service(
        scope
    ).require(
        WorkspacePermission
        .MEETINGS_MANAGE
        .value
    )

    return await meeting_service(
        scope
    ).update_meeting(
        payload,
        meeting_id=meeting_id,
    )


@router.post(
    "/{meeting_id}/start",
    response_model=MeetingResponse,
    summary="Start meeting",
)
async def start_meeting(
    meeting_id: uuid.UUID,
    scope: TenantScope,
) -> MeetingResponse:
    permission_service(
        scope
    ).require(
        WorkspacePermission
        .MEETINGS_MANAGE
        .value
    )

    return await meeting_service(
        scope
    ).start_meeting(
        meeting_id=meeting_id
    )


@router.post(
    "/{meeting_id}/end",
    response_model=MeetingResponse,
    summary="End meeting",
)
async def end_meeting(
    meeting_id: uuid.UUID,
    scope: TenantScope,
) -> MeetingResponse:
    permission_service(
        scope
    ).require(
        WorkspacePermission
        .MEETINGS_MANAGE
        .value
    )

    return await meeting_service(
        scope
    ).end_meeting(
        meeting_id=meeting_id
    )


@router.post(
    "/{meeting_id}/cancel",
    response_model=MeetingResponse,
    summary="Cancel meeting",
)
async def cancel_meeting(
    meeting_id: uuid.UUID,
    scope: TenantScope,
) -> MeetingResponse:
    permission_service(
        scope
    ).require(
        WorkspacePermission
        .MEETINGS_MANAGE
        .value
    )

    return await meeting_service(
        scope
    ).cancel_meeting(
        meeting_id=meeting_id
    )


@router.post(
    "/{meeting_id}/participants",
    response_model=(
        MeetingParticipantResponse
    ),
    status_code=status.HTTP_201_CREATED,
    summary="Add meeting participant",
)
async def add_participant(
    meeting_id: uuid.UUID,
    payload: MeetingParticipantAddRequest,
    scope: TenantScope,
) -> MeetingParticipantResponse:
    permission_service(
        scope
    ).require(
        WorkspacePermission
        .MEETINGS_MANAGE
        .value
    )

    return await meeting_service(
        scope
    ).add_participant(
        payload,
        meeting_id=meeting_id,
    )


@router.patch(
    (
        "/{meeting_id}/participants/"
        "{employee_id}/status"
    ),
    response_model=(
        MeetingParticipantResponse
    ),
    summary="Update participant status",
)
async def update_participant_status(
    meeting_id: uuid.UUID,
    employee_id: uuid.UUID,
    payload: MeetingParticipantStatusRequest,
    scope: TenantScope,
) -> MeetingParticipantResponse:
    permission_service(
        scope
    ).require(
        WorkspacePermission
        .MEETINGS_MANAGE
        .value
    )

    return await meeting_service(
        scope
    ).update_participant_status(
        payload,
        meeting_id=meeting_id,
        employee_id=employee_id,
    )


@router.delete(
    (
        "/{meeting_id}/participants/"
        "{employee_id}"
    ),
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove meeting participant",
)
async def remove_participant(
    meeting_id: uuid.UUID,
    employee_id: uuid.UUID,
    scope: TenantScope,
) -> Response:
    permission_service(
        scope
    ).require(
        WorkspacePermission
        .MEETINGS_MANAGE
        .value
    )

    await meeting_service(
        scope
    ).remove_participant(
        meeting_id=meeting_id,
        employee_id=employee_id,
    )

    return Response(
        status_code=(
            status.HTTP_204_NO_CONTENT
        )
    )


__all__ = [
    "router",
]