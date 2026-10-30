from __future__ import annotations

import logging
import uuid

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Response,
    status,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.core.database import (
    get_control_db,
)
from app.modules.auth.models import User
from app.modules.auth.permissions import (
    get_current_verified_user,
)

from .read_state_router import (
    router as read_state_router,
)
from .realtime_events import (
    channel_realtime_events,
)
from .schemas import (
    WorkspaceChannelCreateRequest,
    WorkspaceChannelMessageCreateRequest,
    WorkspaceChannelMessagePublic,
    WorkspaceChannelMessageUpdateRequest,
    WorkspaceChannelPublic,
    WorkspaceChannelUpdateRequest,
)
from .service import (
    WorkspaceChannelConflictError,
    WorkspaceChannelError,
    WorkspaceChannelNotFoundError,
    WorkspaceChannelPermissionError,
    WorkspaceChannelService,
)


logger = logging.getLogger(
    __name__
)


router = APIRouter(
    prefix="/workspace-channels",
    tags=[
        "Workspace Channels",
    ],
)


def translate_channel_error(
    exc: Exception,
) -> HTTPException:
    if isinstance(
        exc,
        WorkspaceChannelNotFoundError,
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
        WorkspaceChannelPermissionError,
    ):
        return HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=str(
                exc
            ),
        )

    if isinstance(
        exc,
        WorkspaceChannelConflictError,
    ):
        return HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
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


async def _publish_channel_created(
    *,
    channel: WorkspaceChannelPublic,
    actor_user_id: uuid.UUID,
) -> None:
    try:
        await (
            channel_realtime_events
            .channel_created(
                channel=channel,
                actor_user_id=actor_user_id,
            )
        )
    except Exception:
        logger.exception(
            "channel_realtime_publish_failed "
            "event=channel.created "
            "workspace_id=%s channel_id=%s",
            channel.workspace_id,
            channel.id,
        )


async def _publish_channel_updated(
    *,
    channel: WorkspaceChannelPublic,
    actor_user_id: uuid.UUID,
) -> None:
    try:
        await (
            channel_realtime_events
            .channel_updated(
                channel=channel,
                actor_user_id=actor_user_id,
            )
        )
    except Exception:
        logger.exception(
            "channel_realtime_publish_failed "
            "event=channel.updated "
            "workspace_id=%s channel_id=%s",
            channel.workspace_id,
            channel.id,
        )


async def _publish_channel_archived(
    *,
    channel: WorkspaceChannelPublic,
    actor_user_id: uuid.UUID,
) -> None:
    try:
        await (
            channel_realtime_events
            .channel_archived(
                channel=channel,
                actor_user_id=actor_user_id,
            )
        )
    except Exception:
        logger.exception(
            "channel_realtime_publish_failed "
            "event=channel.archived "
            "workspace_id=%s channel_id=%s",
            channel.workspace_id,
            channel.id,
        )


async def _publish_message_created(
    *,
    workspace_id: uuid.UUID,
    message: WorkspaceChannelMessagePublic,
    actor_user_id: uuid.UUID,
) -> None:
    try:
        await (
            channel_realtime_events
            .message_created(
                workspace_id=workspace_id,
                message=message,
                actor_user_id=actor_user_id,
            )
        )
    except Exception:
        logger.exception(
            "channel_realtime_publish_failed "
            "event=message.created "
            "workspace_id=%s "
            "channel_id=%s "
            "message_id=%s",
            workspace_id,
            message.channel_id,
            message.id,
        )


async def _publish_message_updated(
    *,
    workspace_id: uuid.UUID,
    message: WorkspaceChannelMessagePublic,
    actor_user_id: uuid.UUID,
) -> None:
    try:
        await (
            channel_realtime_events
            .message_updated(
                workspace_id=workspace_id,
                message=message,
                actor_user_id=actor_user_id,
            )
        )
    except Exception:
        logger.exception(
            "channel_realtime_publish_failed "
            "event=message.updated "
            "workspace_id=%s "
            "channel_id=%s "
            "message_id=%s",
            workspace_id,
            message.channel_id,
            message.id,
        )


async def _publish_message_deleted(
    *,
    workspace_id: uuid.UUID,
    message: WorkspaceChannelMessagePublic,
    actor_user_id: uuid.UUID,
) -> None:
    try:
        await (
            channel_realtime_events
            .message_deleted(
                workspace_id=workspace_id,
                message=message,
                actor_user_id=actor_user_id,
            )
        )
    except Exception:
        logger.exception(
            "channel_realtime_publish_failed "
            "event=message.deleted "
            "workspace_id=%s "
            "channel_id=%s "
            "message_id=%s",
            workspace_id,
            message.channel_id,
            message.id,
        )


@router.post(
    "",
    response_model=WorkspaceChannelPublic,
    status_code=status.HTTP_201_CREATED,
)
async def create_workspace_channel(
    request: WorkspaceChannelCreateRequest,
    session: AsyncSession = Depends(
        get_control_db
    ),
    user: User = Depends(
        get_current_verified_user
    ),
) -> WorkspaceChannelPublic:
    service = WorkspaceChannelService(
        session
    )

    try:
        channel = await service.create_channel(
            workspace_id=request.workspace_id,
            user_id=user.id,
            name=request.name,
            channel_type=request.channel_type,
        )

        public = (
            WorkspaceChannelPublic
            .model_validate(
                channel
            )
        )

        await session.commit()

    except WorkspaceChannelError as exc:
        await session.rollback()

        raise translate_channel_error(
            exc
        ) from exc

    await _publish_channel_created(
        channel=public,
        actor_user_id=user.id,
    )

    return public


@router.get(
    "/workspace/{workspace_id}",
    response_model=list[
        WorkspaceChannelPublic
    ],
)
async def list_workspace_channels(
    workspace_id: uuid.UUID,
    session: AsyncSession = Depends(
        get_control_db
    ),
    user: User = Depends(
        get_current_verified_user
    ),
) -> list[
    WorkspaceChannelPublic
]:
    service = WorkspaceChannelService(
        session
    )

    channels = await service.list_channels(
        workspace_id=workspace_id,
        user_id=user.id,
    )

    return [
        WorkspaceChannelPublic.model_validate(
            channel
        )
        for channel in channels
    ]


@router.patch(
    "/{channel_id}",
    response_model=WorkspaceChannelPublic,
)
async def rename_workspace_channel(
    channel_id: uuid.UUID,
    request: WorkspaceChannelUpdateRequest,
    session: AsyncSession = Depends(
        get_control_db
    ),
    user: User = Depends(
        get_current_verified_user
    ),
) -> WorkspaceChannelPublic:
    service = WorkspaceChannelService(
        session
    )

    try:
        channel = await service.rename_channel(
            channel_id=channel_id,
            user_id=user.id,
            name=request.name,
        )

        public = (
            WorkspaceChannelPublic
            .model_validate(
                channel
            )
        )

        await session.commit()

    except WorkspaceChannelError as exc:
        await session.rollback()

        raise translate_channel_error(
            exc
        ) from exc

    await _publish_channel_updated(
        channel=public,
        actor_user_id=user.id,
    )

    return public


@router.delete(
    "/{channel_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def archive_workspace_channel(
    channel_id: uuid.UUID,
    session: AsyncSession = Depends(
        get_control_db
    ),
    user: User = Depends(
        get_current_verified_user
    ),
) -> Response:
    service = WorkspaceChannelService(
        session
    )

    try:
        channel = await service.archive_channel(
            channel_id=channel_id,
            user_id=user.id,
        )

        public = (
            WorkspaceChannelPublic
            .model_validate(
                channel
            )
        )

        await session.commit()

    except WorkspaceChannelError as exc:
        await session.rollback()

        raise translate_channel_error(
            exc
        ) from exc

    await _publish_channel_archived(
        channel=public,
        actor_user_id=user.id,
    )

    return Response(
        status_code=(
            status.HTTP_204_NO_CONTENT
        )
    )


@router.post(
    "/{channel_id}/messages",
    response_model=(
        WorkspaceChannelMessagePublic
    ),
    status_code=(
        status.HTTP_201_CREATED
    ),
)
async def send_channel_message(
    channel_id: uuid.UUID,
    request: WorkspaceChannelMessageCreateRequest,
    session: AsyncSession = Depends(
        get_control_db
    ),
    user: User = Depends(
        get_current_verified_user
    ),
) -> WorkspaceChannelMessagePublic:
    service = WorkspaceChannelService(
        session
    )

    try:
        channel = (
            await service._require_channel(
                channel_id
            )
        )

        message = await service.send_message(
            channel_id=channel_id,
            user_id=user.id,
            content=request.content,
        )

        public = (
            WorkspaceChannelMessagePublic
            .model_validate(
                message
            )
        )

        workspace_id = (
            channel.workspace_id
        )

        await session.commit()

    except WorkspaceChannelError as exc:
        await session.rollback()

        raise translate_channel_error(
            exc
        ) from exc

    await _publish_message_created(
        workspace_id=workspace_id,
        message=public,
        actor_user_id=user.id,
    )

    return public


@router.patch(
    "/{channel_id}/messages/{message_id}",
    response_model=(
        WorkspaceChannelMessagePublic
    ),
)
async def update_channel_message(
    channel_id: uuid.UUID,
    message_id: uuid.UUID,
    request:
        WorkspaceChannelMessageUpdateRequest,
    session: AsyncSession = Depends(
        get_control_db
    ),
    user: User = Depends(
        get_current_verified_user
    ),
) -> WorkspaceChannelMessagePublic:
    service = WorkspaceChannelService(
        session
    )

    try:
        channel = (
            await service._require_channel(
                channel_id
            )
        )

        message = (
            await service.update_message(
                channel_id=channel_id,
                message_id=message_id,
                user_id=user.id,
                content=request.content,
            )
        )

        public = (
            WorkspaceChannelMessagePublic
            .model_validate(
                message
            )
        )

        workspace_id = (
            channel.workspace_id
        )

        await session.commit()

    except WorkspaceChannelError as exc:
        await session.rollback()

        raise translate_channel_error(
            exc
        ) from exc

    await _publish_message_updated(
        workspace_id=workspace_id,
        message=public,
        actor_user_id=user.id,
    )

    return public


@router.delete(
    "/{channel_id}/messages/{message_id}",
    status_code=(
        status.HTTP_204_NO_CONTENT
    ),
)
async def delete_channel_message(
    channel_id: uuid.UUID,
    message_id: uuid.UUID,
    session: AsyncSession = Depends(
        get_control_db
    ),
    user: User = Depends(
        get_current_verified_user
    ),
) -> Response:
    service = WorkspaceChannelService(
        session
    )

    try:
        channel = (
            await service._require_channel(
                channel_id
            )
        )

        message = (
            await service.delete_message(
                channel_id=channel_id,
                message_id=message_id,
                user_id=user.id,
            )
        )

        public = (
            WorkspaceChannelMessagePublic
            .model_validate(
                message
            )
        )

        workspace_id = (
            channel.workspace_id
        )

        await session.commit()

    except WorkspaceChannelError as exc:
        await session.rollback()

        raise translate_channel_error(
            exc
        ) from exc

    await _publish_message_deleted(
        workspace_id=workspace_id,
        message=public,
        actor_user_id=user.id,
    )

    return Response(
        status_code=(
            status.HTTP_204_NO_CONTENT
        )
    )


@router.get(
    "/{channel_id}/messages",
    response_model=list[
        WorkspaceChannelMessagePublic
    ],
)
async def list_channel_messages(
    channel_id: uuid.UUID,
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
    ),
    session: AsyncSession = Depends(
        get_control_db
    ),
    user: User = Depends(
        get_current_verified_user
    ),
) -> list[
    WorkspaceChannelMessagePublic
]:
    service = WorkspaceChannelService(
        session
    )

    try:
        messages = await service.list_messages(
            channel_id=channel_id,
            user_id=user.id,
            limit=limit,
        )

        return [
            WorkspaceChannelMessagePublic
            .model_validate(
                message
            )
            for message in messages
        ]

    except WorkspaceChannelError as exc:
        raise translate_channel_error(
            exc
        ) from exc


router.include_router(
    read_state_router
)


__all__ = [
    "router",
]