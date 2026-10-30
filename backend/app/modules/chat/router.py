from __future__ import annotations

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

from .realtime_publish_service import (
    ChatRealtimePublishService,
)
from .schemas import (
    ChatMessagePublic,
    ConversationMemberPublic,
    ConversationPublic,
    DirectConversationCreateRequest,
    GroupConversationCreateRequest,
    MessageCreateRequest,
    MessageEditRequest,
    MessageReceiptPublic,
    PresencePublic,
    PresenceUpdateRequest,
)
from .service import (
    ChatConflictError,
    ChatPermissionError,
    ChatService,
    ConversationNotFoundError,
)
from .state_service import (
    ChatStateService,
    MessageNotFoundError,
)


router = APIRouter(
    prefix="/chat",
    tags=[
        "Chat",
    ],
)


def translate_chat_error(
    exc: Exception,
) -> HTTPException:
    if isinstance(
        exc,
        (
            ConversationNotFoundError,
            MessageNotFoundError,
        ),
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
        ChatPermissionError,
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
        ChatConflictError,
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


@router.post(
    "/direct",
    response_model=ConversationPublic,
)
async def create_or_get_direct(
    request: DirectConversationCreateRequest,
    session: AsyncSession = Depends(
        get_control_db
    ),
    user: User = Depends(
        get_current_verified_user
    ),
) -> ConversationPublic:
    service = ChatService(
        session
    )

    try:
        conversation = (
            await service.create_or_get_direct(
                current_user_id=user.id,
                target_user_id=(
                    request.target_user_id
                ),
            )
        )

        await session.commit()

        return ConversationPublic.model_validate(
            conversation
        )

    except (
        ConversationNotFoundError,
        ChatPermissionError,
        ChatConflictError,
    ) as exc:
        await session.rollback()

        raise translate_chat_error(
            exc
        ) from exc


@router.post(
    "/groups",
    response_model=ConversationPublic,
    status_code=(
        status.HTTP_201_CREATED
    ),
)
async def create_group(
    request: GroupConversationCreateRequest,
    session: AsyncSession = Depends(
        get_control_db
    ),
    user: User = Depends(
        get_current_verified_user
    ),
) -> ConversationPublic:
    service = ChatService(
        session
    )

    try:
        conversation = (
            await service.create_group(
                current_user_id=user.id,
                name=request.name,
                member_user_ids=(
                    request.member_user_ids
                ),
            )
        )

        await session.commit()

        return ConversationPublic.model_validate(
            conversation
        )

    except (
        ConversationNotFoundError,
        ChatPermissionError,
        ChatConflictError,
    ) as exc:
        await session.rollback()

        raise translate_chat_error(
            exc
        ) from exc


@router.get(
    "/conversations",
    response_model=list[
        ConversationPublic
    ],
)
async def list_conversations(
    session: AsyncSession = Depends(
        get_control_db
    ),
    user: User = Depends(
        get_current_verified_user
    ),
) -> list[
    ConversationPublic
]:
    service = ChatService(
        session
    )

    conversations = (
        await service.list_conversations(
            user_id=user.id
        )
    )

    return [
        ConversationPublic.model_validate(
            item
        )
        for item in conversations
    ]


@router.post(
    "/{conversation_id}/members/{target_user_id}",
    response_model=(
        ConversationMemberPublic
    ),
)
async def add_group_member(
    conversation_id: uuid.UUID,
    target_user_id: uuid.UUID,
    session: AsyncSession = Depends(
        get_control_db
    ),
    user: User = Depends(
        get_current_verified_user
    ),
) -> ConversationMemberPublic:
    service = ChatService(
        session
    )

    try:
        member = (
            await service.add_group_member(
                conversation_id=(
                    conversation_id
                ),
                current_user_id=user.id,
                target_user_id=(
                    target_user_id
                ),
            )
        )

        await session.commit()

        return (
            ConversationMemberPublic
            .model_validate(
                member
            )
        )

    except (
        ConversationNotFoundError,
        ChatPermissionError,
        ChatConflictError,
    ) as exc:
        await session.rollback()

        raise translate_chat_error(
            exc
        ) from exc


@router.delete(
    "/{conversation_id}/members/{target_user_id}",
    status_code=(
        status.HTTP_204_NO_CONTENT
    ),
)
async def remove_group_member(
    conversation_id: uuid.UUID,
    target_user_id: uuid.UUID,
    session: AsyncSession = Depends(
        get_control_db
    ),
    user: User = Depends(
        get_current_verified_user
    ),
) -> Response:
    service = ChatService(
        session
    )

    try:
        await service.remove_group_member(
            conversation_id=(
                conversation_id
            ),
            current_user_id=user.id,
            target_user_id=(
                target_user_id
            ),
        )

        await session.commit()

        return Response(
            status_code=(
                status.HTTP_204_NO_CONTENT
            )
        )

    except (
        ConversationNotFoundError,
        ChatPermissionError,
        ChatConflictError,
    ) as exc:
        await session.rollback()

        raise translate_chat_error(
            exc
        ) from exc


@router.post(
    "/{conversation_id}/messages",
    response_model=ChatMessagePublic,
    status_code=(
        status.HTTP_201_CREATED
    ),
)
async def send_message(
    conversation_id: uuid.UUID,
    request: MessageCreateRequest,
    session: AsyncSession = Depends(
        get_control_db
    ),
    user: User = Depends(
        get_current_verified_user
    ),
) -> ChatMessagePublic:
    service = ChatService(
        session
    )

    try:
        message = await service.send_message(
            conversation_id=(
                conversation_id
            ),
            sender_user_id=user.id,
            content=request.content,
        )

        await session.commit()

        publisher = (
            ChatRealtimePublishService()
        )

        await publisher.message_created(
            message=message,
            actor_user_id=user.id,
        )

        return ChatMessagePublic.model_validate(
            message
        )

    except (
        ConversationNotFoundError,
        ChatPermissionError,
        ChatConflictError,
    ) as exc:
        await session.rollback()

        raise translate_chat_error(
            exc
        ) from exc


@router.get(
    "/{conversation_id}/messages",
    response_model=list[
        ChatMessagePublic
    ],
)
async def list_messages(
    conversation_id: uuid.UUID,
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
    ChatMessagePublic
]:
    service = ChatService(
        session
    )

    try:
        messages = await service.list_messages(
            conversation_id=(
                conversation_id
            ),
            user_id=user.id,
            limit=limit,
        )

        return [
            ChatMessagePublic.model_validate(
                item
            )
            for item in messages
        ]

    except (
        ConversationNotFoundError,
        ChatPermissionError,
        ChatConflictError,
    ) as exc:
        raise translate_chat_error(
            exc
        ) from exc


@router.patch(
    "/{conversation_id}/messages/{message_id}",
    response_model=ChatMessagePublic,
)
async def edit_message(
    conversation_id: uuid.UUID,
    message_id: uuid.UUID,
    request: MessageEditRequest,
    session: AsyncSession = Depends(
        get_control_db
    ),
    user: User = Depends(
        get_current_verified_user
    ),
) -> ChatMessagePublic:
    service = ChatStateService(
        session
    )

    try:
        message = await service.edit_message(
            conversation_id=(
                conversation_id
            ),
            message_id=message_id,
            user_id=user.id,
            content=request.content,
        )

        await session.commit()

        publisher = (
            ChatRealtimePublishService()
        )

        await publisher.message_updated(
            message=message,
            actor_user_id=user.id,
        )

        return ChatMessagePublic.model_validate(
            message
        )

    except (
        ConversationNotFoundError,
        MessageNotFoundError,
        ChatPermissionError,
        ChatConflictError,
    ) as exc:
        await session.rollback()

        raise translate_chat_error(
            exc
        ) from exc


@router.delete(
    "/{conversation_id}/messages/{message_id}",
    response_model=ChatMessagePublic,
)
async def delete_message(
    conversation_id: uuid.UUID,
    message_id: uuid.UUID,
    session: AsyncSession = Depends(
        get_control_db
    ),
    user: User = Depends(
        get_current_verified_user
    ),
) -> ChatMessagePublic:
    service = ChatStateService(
        session
    )

    try:
        message = await service.delete_message(
            conversation_id=(
                conversation_id
            ),
            message_id=message_id,
            user_id=user.id,
        )

        await session.commit()

        publisher = (
            ChatRealtimePublishService()
        )

        await publisher.message_deleted(
            message=message,
            actor_user_id=user.id,
        )

        return ChatMessagePublic.model_validate(
            message
        )

    except (
        ConversationNotFoundError,
        MessageNotFoundError,
        ChatPermissionError,
        ChatConflictError,
    ) as exc:
        await session.rollback()

        raise translate_chat_error(
            exc
        ) from exc


@router.post(
    "/{conversation_id}/read/{message_id}",
    response_model=MessageReceiptPublic,
)
async def mark_message_read(
    conversation_id: uuid.UUID,
    message_id: uuid.UUID,
    session: AsyncSession = Depends(
        get_control_db
    ),
    user: User = Depends(
        get_current_verified_user
    ),
) -> MessageReceiptPublic:
    service = ChatStateService(
        session
    )

    try:
        receipt = await service.mark_read(
            conversation_id=(
                conversation_id
            ),
            message_id=message_id,
            user_id=user.id,
        )

        await session.commit()

        publisher = (
            ChatRealtimePublishService()
        )

        await publisher.message_read(
            conversation_id=(
                conversation_id
            ),
            receipt=receipt,
            actor_user_id=user.id,
        )

        return (
            MessageReceiptPublic
            .model_validate(
                receipt
            )
        )

    except (
        ConversationNotFoundError,
        MessageNotFoundError,
        ChatPermissionError,
        ChatConflictError,
    ) as exc:
        await session.rollback()

        raise translate_chat_error(
            exc
        ) from exc


@router.get(
    "/{conversation_id}/read-receipts/{message_id}",
    response_model=list[
        MessageReceiptPublic
    ],
)
async def list_message_receipts(
    conversation_id: uuid.UUID,
    message_id: uuid.UUID,
    session: AsyncSession = Depends(
        get_control_db
    ),
    user: User = Depends(
        get_current_verified_user
    ),
) -> list[
    MessageReceiptPublic
]:
    service = ChatStateService(
        session
    )

    try:
        receipts = await service.list_receipts(
            conversation_id=(
                conversation_id
            ),
            message_id=message_id,
            user_id=user.id,
        )

        return [
            MessageReceiptPublic.model_validate(
                item
            )
            for item in receipts
        ]

    except (
        ConversationNotFoundError,
        MessageNotFoundError,
        ChatPermissionError,
        ChatConflictError,
    ) as exc:
        raise translate_chat_error(
            exc
        ) from exc


@router.put(
    "/presence",
    response_model=PresencePublic,
)
async def update_presence(
    request: PresenceUpdateRequest,
    session: AsyncSession = Depends(
        get_control_db
    ),
    user: User = Depends(
        get_current_verified_user
    ),
) -> PresencePublic:
    service = ChatStateService(
        session
    )

    presence = await service.set_presence(
        user_id=user.id,
        status=request.status,
    )

    await session.commit()

    return PresencePublic.model_validate(
        presence
    )


@router.get(
    "/presence/{target_user_id}",
    response_model=PresencePublic,
)
async def get_presence(
    target_user_id: uuid.UUID,
    session: AsyncSession = Depends(
        get_control_db
    ),
    user: User = Depends(
        get_current_verified_user
    ),
) -> PresencePublic:
    service = ChatStateService(
        session
    )

    try:
        presence = await service.get_presence(
            current_user_id=user.id,
            target_user_id=(
                target_user_id
            ),
        )

        return PresencePublic.model_validate(
            presence
        )

    except (
        ChatPermissionError,
        ConversationNotFoundError,
        MessageNotFoundError,
        ChatConflictError,
    ) as exc:
        raise translate_chat_error(
            exc
        ) from exc



from .group_controls_router import (
    router as group_controls_router,
)

router.include_router(
    group_controls_router,
)
from .group_inbox_router import router as group_inbox_router
router.include_router(group_inbox_router)