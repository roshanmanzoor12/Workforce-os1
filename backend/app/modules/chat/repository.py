from __future__ import annotations

import uuid

from sqlalchemy import (
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.friends.repository import (
    normalize_user_pair,
)

from .enums import (
    ConversationMemberRole,
    ConversationType,
    MessageType,
)
from .models import (
    ChatMessage,
    Conversation,
    ConversationMember,
)


class ChatRepository:
    async def get_conversation(
        self,
        session: AsyncSession,
        *,
        conversation_id: uuid.UUID,
    ) -> Conversation | None:
        result = await session.execute(
            select(
                Conversation
            ).where(
                Conversation.id
                == conversation_id
            )
        )

        return result.scalar_one_or_none()

    async def get_direct_between_users(
        self,
        session: AsyncSession,
        *,
        first_user_id: uuid.UUID,
        second_user_id: uuid.UUID,
    ) -> Conversation | None:
        low_id, high_id = normalize_user_pair(
            first_user_id,
            second_user_id,
        )

        result = await session.execute(
            select(
                Conversation
            ).where(
                Conversation.conversation_type
                == ConversationType.DIRECT,
                Conversation.direct_user_low_id
                == low_id,
                Conversation.direct_user_high_id
                == high_id,
                Conversation.is_active.is_(
                    True
                ),
            )
        )

        return result.scalar_one_or_none()

    async def create_direct(
        self,
        session: AsyncSession,
        *,
        creator_user_id: uuid.UUID,
        target_user_id: uuid.UUID,
    ) -> Conversation:
        low_id, high_id = normalize_user_pair(
            creator_user_id,
            target_user_id,
        )

        conversation = Conversation(
            conversation_type=(
                ConversationType.DIRECT
            ),
            name=None,
            created_by_user_id=(
                creator_user_id
            ),
            direct_user_low_id=low_id,
            direct_user_high_id=high_id,
        )

        session.add(
            conversation
        )

        await session.flush()

        return conversation

    async def create_group(
        self,
        session: AsyncSession,
        *,
        creator_user_id: uuid.UUID,
        name: str,
    ) -> Conversation:
        conversation = Conversation(
            conversation_type=(
                ConversationType.GROUP
            ),
            name=name,
            created_by_user_id=(
                creator_user_id
            ),
        )

        session.add(
            conversation
        )

        await session.flush()

        return conversation

    async def get_member(
        self,
        session: AsyncSession,
        *,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> ConversationMember | None:
        result = await session.execute(
            select(
                ConversationMember
            ).where(
                ConversationMember.conversation_id
                == conversation_id,
                ConversationMember.user_id
                == user_id,
            )
        )

        return result.scalar_one_or_none()

    async def add_member(
        self,
        session: AsyncSession,
        *,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        role: ConversationMemberRole,
    ) -> ConversationMember:
        existing = await self.get_member(
            session,
            conversation_id=conversation_id,
            user_id=user_id,
        )

        if existing is not None:
            existing.role = role
            existing.left_at = None

            await session.flush()

            return existing

        member = ConversationMember(
            conversation_id=conversation_id,
            user_id=user_id,
            role=role,
        )

        session.add(
            member
        )

        await session.flush()

        return member

    async def list_conversations_for_user(
        self,
        session: AsyncSession,
        *,
        user_id: uuid.UUID,
    ) -> list[Conversation]:
        result = await session.execute(
            select(
                Conversation
            )
            .join(
                ConversationMember,
                ConversationMember.conversation_id
                == Conversation.id,
            )
            .where(
                ConversationMember.user_id
                == user_id,
                ConversationMember.left_at.is_(
                    None
                ),
                Conversation.is_active.is_(
                    True
                ),
            )
            .order_by(
                Conversation.updated_at.desc()
            )
        )

        return list(
            result.scalars().all()
        )

    async def create_message(
        self,
        session: AsyncSession,
        *,
        conversation_id: uuid.UUID,
        sender_user_id: uuid.UUID,
        content: str,
    ) -> ChatMessage:
        message = ChatMessage(
            conversation_id=conversation_id,
            sender_user_id=sender_user_id,
            message_type=MessageType.TEXT,
            content=content,
        )

        session.add(
            message
        )

        await session.flush()

        return message

    async def list_messages(
        self,
        session: AsyncSession,
        *,
        conversation_id: uuid.UUID,
        limit: int,
    ) -> list[ChatMessage]:
        result = await session.execute(
            select(
                ChatMessage
            )
            .where(
                ChatMessage.conversation_id
                == conversation_id,
                ChatMessage.deleted_at.is_(
                    None
                ),
            )
            .order_by(
                ChatMessage.created_at.desc()
            )
            .limit(
                limit
            )
        )

        messages = list(
            result.scalars().all()
        )

        messages.reverse()

        return messages


__all__ = [
    "ChatRepository",
]