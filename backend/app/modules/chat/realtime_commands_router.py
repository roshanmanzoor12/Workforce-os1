from __future__ import annotations

import logging
import uuid

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from redis.exceptions import RedisError as RedisClientError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_control_db
from app.modules.auth.models import User
from app.modules.auth.permissions import (
    get_current_verified_user,
)

from .chat_redis import get_chat_redis
from .pagination_schemas import ChatMessagePagePublic
from .realtime_command_schemas import (
    HeartbeatResponse,
    RealtimeActionResponse,
    TypingUsersResponse,
)
from .realtime_presence import RealtimePresenceTracker
from .realtime_publish_service import ChatRealtimePublishService
from .realtime_resume import RealtimeResumeService
from .realtime_client_schemas import RealtimeResumeRequest
from .schemas import ChatMessagePublic
from .service import (
    ChatPermissionError,
    ConversationNotFoundError,
)
from .typing_command_service import TypingCommandService
from .typing_service import TypingService


logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/chat/realtime",
    tags=["Chat Realtime"],
)


def translate_realtime_error(
    exc: Exception,
) -> HTTPException:
    if isinstance(exc, ConversationNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    if isinstance(exc, ChatPermissionError):
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )

    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(exc),
    )


def build_typing_command_service(
    session: AsyncSession,
) -> TypingCommandService:
    redis_client = get_chat_redis()

    return TypingCommandService(
        session,
        typing_service=TypingService(
            redis_client
        ),
    )


@router.post(
    "/typing/{conversation_id}/start",
    response_model=RealtimeActionResponse,
)
async def start_typing(
    conversation_id: uuid.UUID,
    session: AsyncSession = Depends(
        get_control_db
    ),
    user: User = Depends(
        get_current_verified_user
    ),
) -> RealtimeActionResponse:
    service = build_typing_command_service(
        session
    )

    try:
        await service.start(
            conversation_id=conversation_id,
            user_id=user.id,
        )

        return RealtimeActionResponse(
            success=True,
        )

    except (
        ConversationNotFoundError,
        ChatPermissionError,
    ) as exc:
        raise translate_realtime_error(exc) from exc

    except RedisClientError as exc:
        logger.exception(
            "Realtime Redis command failed"
        )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Realtime service is temporarily unavailable.",
        ) from exc


@router.post(
    "/typing/{conversation_id}/stop",
    response_model=RealtimeActionResponse,
)
async def stop_typing(
    conversation_id: uuid.UUID,
    session: AsyncSession = Depends(
        get_control_db
    ),
    user: User = Depends(
        get_current_verified_user
    ),
) -> RealtimeActionResponse:
    service = build_typing_command_service(
        session
    )

    try:
        await service.stop(
            conversation_id=conversation_id,
            user_id=user.id,
        )

        return RealtimeActionResponse(
            success=True,
        )

    except (
        ConversationNotFoundError,
        ChatPermissionError,
    ) as exc:
        raise translate_realtime_error(exc) from exc

    except RedisClientError as exc:
        logger.exception(
            "Realtime Redis command failed"
        )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Realtime service is temporarily unavailable.",
        ) from exc


@router.get(
    "/typing/{conversation_id}",
    response_model=TypingUsersResponse,
)
async def list_typing_users(
    conversation_id: uuid.UUID,
    session: AsyncSession = Depends(
        get_control_db
    ),
    user: User = Depends(
        get_current_verified_user
    ),
) -> TypingUsersResponse:
    service = build_typing_command_service(
        session
    )

    try:
        user_ids = await service.list_users(
            conversation_id=conversation_id,
            user_id=user.id,
        )

        return TypingUsersResponse(
            user_ids=user_ids,
        )

    except (
        ConversationNotFoundError,
        ChatPermissionError,
    ) as exc:
        raise translate_realtime_error(exc) from exc

    except RedisClientError as exc:
        logger.exception(
            "Realtime Redis command failed"
        )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Realtime service is temporarily unavailable.",
        ) from exc


@router.post(
    "/heartbeat",
    response_model=HeartbeatResponse,
)
async def realtime_heartbeat(
    user: User = Depends(
        get_current_verified_user
    ),
) -> HeartbeatResponse:
    try:
        redis_client = get_chat_redis()

        tracker = RealtimePresenceTracker(
            redis_client
        )

        was_online = await tracker.is_online(
            user_id=user.id,
        )

        heartbeat_unix = await tracker.heartbeat(
            user_id=user.id,
        )

        announcement_key = (
            "workforceos:chat:presence-announced:v1:"
            f"{user.id}"
        )

        announced = await redis_client.get(
            announcement_key
        )

        # Refresh presence on every heartbeat, but avoid sending
        # an online announcement on every request. Failed
        # publications remain eligible for another attempt.
        if (
            not was_online
            or announced not in (
                "online",
                b"online",
            )
        ):
            published = (
                await ChatRealtimePublishService().presence_updated(
                    actor_user_id=user.id,
                    online=True,
                )
            )

            if published:
                await redis_client.set(
                    announcement_key,
                    "online",
                    ex=tracker.ttl_seconds,
                )

        return HeartbeatResponse(
            online=True,
            heartbeat_unix=heartbeat_unix,
            expires_in_seconds=tracker.ttl_seconds,
        )

    except RedisClientError as exc:
        logger.exception(
            "Realtime heartbeat Redis operation failed"
        )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Realtime presence service is temporarily unavailable."
            ),
        ) from exc


@router.post(
    "/resume",
    response_model=ChatMessagePagePublic,
)
async def resume_realtime_conversation(
    request: RealtimeResumeRequest,
    session: AsyncSession = Depends(
        get_control_db
    ),
    user: User = Depends(
        get_current_verified_user
    ),
) -> ChatMessagePagePublic:
    service = RealtimeResumeService(
        session
    )

    try:
        result = await service.resume_conversation(
            conversation_id=request.conversation_id,
            user_id=user.id,
            cursor=request.cursor,
            limit=request.limit,
        )

    except (
        ConversationNotFoundError,
        ChatPermissionError,
        ValueError,
    ) as exc:
        raise translate_realtime_error(exc) from exc

    except RedisClientError as exc:
        logger.exception(
            "Realtime Redis command failed"
        )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Realtime service is temporarily unavailable.",
        ) from exc

    return ChatMessagePagePublic(
        items=[
            ChatMessagePublic.model_validate(
                message
            )
            for message in result.page.items
        ],
        next_cursor=result.page.next_cursor,
        has_more=result.page.has_more,
    )


__all__ = [
    "router",
]