from __future__ import annotations

import uuid
from datetime import (
    datetime,
    timezone,
)

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.friends.service import (
    FriendshipService,
)

from .enums import PresenceStatus
from .models import (
    ChatMessage,
    ChatMessageReceipt,
    ChatPresence,
)
from .repository import ChatRepository
from .service import (
    ChatConflictError,
    ChatPermissionError,
    ConversationNotFoundError,
)
from .state_repository import (
    ChatStateRepository,
)


class MessageNotFoundError(
    ValueError
):
    pass


class ChatStateService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        repository: ChatStateRepository | None = None,
        chat_repository: ChatRepository | None = None,
        friendship_service: FriendshipService | None = None,
    ) -> None:
        self.session = session

        self.repository = (
            repository
            or ChatStateRepository()
        )

        self.chat_repository = (
            chat_repository
            or ChatRepository()
        )

        self.friendship_service = (
            friendship_service
            or FriendshipService(
                session
            )
        )

    async def edit_message(
        self,
        *,
        conversation_id: uuid.UUID,
        message_id: uuid.UUID,
        user_id: uuid.UUID,
        content: str,
    ) -> ChatMessage:
        await self._require_active_member(
            conversation_id=conversation_id,
            user_id=user_id,
        )

        message = await self._require_message(
            message_id
        )

        if (
            message.conversation_id
            != conversation_id
        ):
            raise MessageNotFoundError(
                "Message not found in conversation."
            )

        if (
            message.sender_user_id
            != user_id
        ):
            raise ChatPermissionError(
                "Only the message sender can "
                "edit this message."
            )

        if message.deleted_at is not None:
            raise ChatConflictError(
                "Deleted messages cannot be edited."
            )

        message.content = content

        message.edited_at = datetime.now(
            timezone.utc
        )

        await self.session.flush()

        return message

    async def delete_message(
        self,
        *,
        conversation_id: uuid.UUID,
        message_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> ChatMessage:
        await self._require_active_member(
            conversation_id=conversation_id,
            user_id=user_id,
        )

        message = await self._require_message(
            message_id
        )

        if (
            message.conversation_id
            != conversation_id
        ):
            raise MessageNotFoundError(
                "Message not found in conversation."
            )

        if (
            message.sender_user_id
            != user_id
        ):
            raise ChatPermissionError(
                "Only the message sender can "
                "delete this message."
            )

        if message.deleted_at is None:
            message.deleted_at = datetime.now(
                timezone.utc
            )

            message.content = ""

        await self.session.flush()

        return message

    async def mark_read(
        self,
        *,
        conversation_id: uuid.UUID,
        message_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> ChatMessageReceipt:
        await self._require_active_member(
            conversation_id=conversation_id,
            user_id=user_id,
        )

        message = await self._require_message(
            message_id
        )

        if (
            message.conversation_id
            != conversation_id
        ):
            raise MessageNotFoundError(
                "Message not found in conversation."
            )

        return await self.repository.save_receipt(
            self.session,
            message_id=message_id,
            user_id=user_id,
        )

    async def list_receipts(
        self,
        *,
        conversation_id: uuid.UUID,
        message_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> list[ChatMessageReceipt]:
        await self._require_active_member(
            conversation_id=conversation_id,
            user_id=user_id,
        )

        message = await self._require_message(
            message_id
        )

        if (
            message.conversation_id
            != conversation_id
        ):
            raise MessageNotFoundError(
                "Message not found in conversation."
            )

        return await self.repository.list_receipts(
            self.session,
            message_id=message_id,
        )

    async def set_presence(
        self,
        *,
        user_id: uuid.UUID,
        status: PresenceStatus,
    ) -> ChatPresence:
        presence = (
            await self.repository
            .ensure_presence(
                self.session,
                user_id=user_id,
            )
        )

        now = datetime.now(
            timezone.utc
        )

        presence.status = status
        presence.updated_at = now

        if (
            status
            == PresenceStatus.OFFLINE
        ):
            presence.last_seen_at = now

        await self.session.flush()

        return presence

    async def get_presence(
        self,
        *,
        current_user_id: uuid.UUID,
        target_user_id: uuid.UUID,
    ) -> ChatPresence:
        if (
            current_user_id
            != target_user_id
        ):
            are_friends = (
                await self.friendship_service
                .are_friends(
                    first_user_id=(
                        current_user_id
                    ),
                    second_user_id=(
                        target_user_id
                    ),
                )
            )

            if not are_friends:
                raise ChatPermissionError(
                    "Presence is only visible "
                    "to accepted friends."
                )

        presence = (
            await self.repository
            .ensure_presence(
                self.session,
                user_id=target_user_id,
            )
        )

        return presence

    async def _require_message(
        self,
        message_id: uuid.UUID,
    ) -> ChatMessage:
        message = (
            await self.repository.get_message(
                self.session,
                message_id=message_id,
            )
        )

        if message is None:
            raise MessageNotFoundError(
                "Message not found."
            )

        return message

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
                conversation_id=conversation_id,
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
            await self.chat_repository.get_member(
                self.session,
                conversation_id=conversation_id,
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
    "ChatStateService",
    "MessageNotFoundError",
]