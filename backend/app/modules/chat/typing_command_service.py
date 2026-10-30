from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from .repository import (
    ChatRepository,
)
from .realtime_publish_service import (
    ChatRealtimePublishService,
)
from .service import (
    ChatPermissionError,
    ConversationNotFoundError,
)
from .typing_service import (
    TypingService,
)


class TypingCommandService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        typing_service: TypingService,
        chat_repository: ChatRepository | None = None,
        publisher: (
            ChatRealtimePublishService
            | None
        ) = None,
    ) -> None:
        self.session = session

        self.typing_service = typing_service

        self.chat_repository = (
            chat_repository
            or ChatRepository()
        )

        self.publisher = (
            publisher
            or ChatRealtimePublishService()
        )

    async def start(
        self,
        *,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        await self._require_active_member(
            conversation_id=conversation_id,
            user_id=user_id,
        )

        await self.typing_service.start_typing(
            conversation_id=conversation_id,
            user_id=user_id,
        )

        await self.publisher.typing_started(
            conversation_id=conversation_id,
            actor_user_id=user_id,
        )

    async def stop(
        self,
        *,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        await self._require_active_member(
            conversation_id=conversation_id,
            user_id=user_id,
        )

        await self.typing_service.stop_typing(
            conversation_id=conversation_id,
            user_id=user_id,
        )

        await self.publisher.typing_stopped(
            conversation_id=conversation_id,
            actor_user_id=user_id,
        )

    async def list_users(
        self,
        *,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> list[
        uuid.UUID
    ]:
        await self._require_active_member(
            conversation_id=conversation_id,
            user_id=user_id,
        )

        users = (
            await self.typing_service
            .list_typing_users(
                conversation_id=(
                    conversation_id
                )
            )
        )

        return [
            typing_user_id
            for typing_user_id in users
            if typing_user_id
            != user_id
        ]

    async def _require_active_member(
        self,
        *,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        conversation = (
            await self.chat_repository
            .get_conversation(
                self.session,
                conversation_id=(
                    conversation_id
                ),
            )
        )

        if (
            conversation is None
            or not conversation.is_active
        ):
            raise ConversationNotFoundError(
                "Conversation not found."
            )

        member = (
            await self.chat_repository
            .get_member(
                self.session,
                conversation_id=(
                    conversation_id
                ),
                user_id=user_id,
            )
        )

        if (
            member is None
            or member.left_at is not None
        ):
            raise ChatPermissionError(
                "User is not an active member "
                "of this conversation."
            )


__all__ = [
    "TypingCommandService",
]