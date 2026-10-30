from __future__ import annotations

import uuid

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.core.database import (
    get_control_db,
)
from app.modules.auth.models import (
    User,
)
from app.modules.auth.permissions import (
    get_current_verified_user,
)

from .read_state_schemas import (
    WorkspaceChannelReadStatePublic,
    WorkspaceChannelUnreadListResponse,
    WorkspaceChannelUnreadSummary,
)
from .read_state_service import (
    WorkspaceChannelReadStateError,
    WorkspaceChannelReadStateNotFoundError,
    WorkspaceChannelReadStatePermissionError,
    WorkspaceChannelReadStateService,
)


router = APIRouter(
    tags=[
        "Workspace Channel Read State",
    ],
)


def _translate(
    exc: Exception,
) -> HTTPException:
    if isinstance(
        exc,
        WorkspaceChannelReadStateNotFoundError,
    ):
        return HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=str(
                exc
            ),
        )

    if isinstance(
        exc,
        WorkspaceChannelReadStatePermissionError,
    ):
        return HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=str(
                exc
            ),
        )

    return HTTPException(
        status_code=(
            status.HTTP_400_BAD_REQUEST
        ),
        detail=str(
            exc
        ),
    )


@router.get(
    "/workspace/{workspace_id}/read-state",
    response_model=(
        WorkspaceChannelUnreadListResponse
    ),
)
async def list_workspace_channel_read_state(
    workspace_id: uuid.UUID,
    session: AsyncSession = Depends(
        get_control_db
    ),
    user: User = Depends(
        get_current_verified_user
    ),
) -> WorkspaceChannelUnreadListResponse:
    service = (
        WorkspaceChannelReadStateService(
            session
        )
    )

    try:
        return await service.list_workspace(
            workspace_id=workspace_id,
            user_id=user.id,
        )

    except WorkspaceChannelReadStateError as exc:
        raise _translate(
            exc
        ) from exc


@router.get(
    "/{channel_id}/read-state",
    response_model=(
        WorkspaceChannelUnreadSummary
    ),
)
async def get_channel_read_state(
    channel_id: uuid.UUID,
    session: AsyncSession = Depends(
        get_control_db
    ),
    user: User = Depends(
        get_current_verified_user
    ),
) -> WorkspaceChannelUnreadSummary:
    service = (
        WorkspaceChannelReadStateService(
            session
        )
    )

    try:
        return await service.get_summary(
            channel_id=channel_id,
            user_id=user.id,
        )

    except WorkspaceChannelReadStateError as exc:
        raise _translate(
            exc
        ) from exc


@router.post(
    "/{channel_id}/read/{message_id}",
    response_model=(
        WorkspaceChannelReadStatePublic
    ),
)
async def mark_channel_message_read(
    channel_id: uuid.UUID,
    message_id: uuid.UUID,
    session: AsyncSession = Depends(
        get_control_db
    ),
    user: User = Depends(
        get_current_verified_user
    ),
) -> WorkspaceChannelReadStatePublic:
    service = (
        WorkspaceChannelReadStateService(
            session
        )
    )

    try:
        result = (
            await service.mark_message_read(
                channel_id=channel_id,
                message_id=message_id,
                user_id=user.id,
            )
        )

        await session.commit()

        return result

    except WorkspaceChannelReadStateError as exc:
        await session.rollback()

        raise _translate(
            exc
        ) from exc


@router.post(
    "/{channel_id}/read-all",
    response_model=(
        WorkspaceChannelReadStatePublic
    ),
)
async def mark_channel_read_all(
    channel_id: uuid.UUID,
    session: AsyncSession = Depends(
        get_control_db
    ),
    user: User = Depends(
        get_current_verified_user
    ),
) -> WorkspaceChannelReadStatePublic:
    service = (
        WorkspaceChannelReadStateService(
            session
        )
    )

    try:
        result = (
            await service.mark_all_read(
                channel_id=channel_id,
                user_id=user.id,
            )
        )

        await session.commit()

        return result

    except WorkspaceChannelReadStateError as exc:
        await session.rollback()

        raise _translate(
            exc
        ) from exc


__all__ = [
    "router",
]