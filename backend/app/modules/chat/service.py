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

from .enums import (
    ConversationMemberRole,
    ConversationType,
)
from .models import (
    ChatMessage,
    Conversation,
    ConversationMember,
)
from .repository import (
    ChatRepository,
)


class ChatError(
    ValueError
):
    pass


class ConversationNotFoundError(
    ChatError
):
    pass


class ChatPermissionError(
    ChatError
):
    pass


class ChatConflictError(
    ChatError
):
    pass


class ChatService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        repository: ChatRepository | None = None,
        friendship_service: FriendshipService | None = None,
    ) -> None:
        self.session = session

        self.repository = (
            repository
            or ChatRepository()
        )

        self.friendship_service = (
            friendship_service
            or FriendshipService(
                session
            )
        )

    async def create_or_get_direct(
        self,
        *,
        current_user_id: uuid.UUID,
        target_user_id: uuid.UUID,
    ) -> Conversation:
        if (
            current_user_id
            == target_user_id
        ):
            raise ChatConflictError(
                "A direct conversation requires "
                "two different users."
            )

        if not await self.friendship_service.are_friends(
            first_user_id=current_user_id,
            second_user_id=target_user_id,
        ):
            raise ChatPermissionError(
                "Direct messages require an "
                "accepted friendship."
            )

        existing = (
            await self.repository
            .get_direct_between_users(
                self.session,
                first_user_id=current_user_id,
                second_user_id=target_user_id,
            )
        )

        if existing is not None:
            return existing

        conversation = (
            await self.repository.create_direct(
                self.session,
                creator_user_id=(
                    current_user_id
                ),
                target_user_id=(
                    target_user_id
                ),
            )
        )

        await self.repository.add_member(
            self.session,
            conversation_id=conversation.id,
            user_id=current_user_id,
            role=ConversationMemberRole.MEMBER,
        )

        await self.repository.add_member(
            self.session,
            conversation_id=conversation.id,
            user_id=target_user_id,
            role=ConversationMemberRole.MEMBER,
        )

        return conversation

    async def create_group(
        self,
        *,
        current_user_id: uuid.UUID,
        name: str,
        member_user_ids: list[uuid.UUID],
    ) -> Conversation:
        unique_members = list(
            dict.fromkeys(
                member_user_ids
            )
        )

        unique_members = [
            user_id
            for user_id in unique_members
            if user_id != current_user_id
        ]

        if not unique_members:
            raise ChatConflictError(
                "Group requires at least one "
                "other member."
            )

        for member_user_id in unique_members:
            allowed = (
                await self.friendship_service
                .are_friends(
                    first_user_id=(
                        current_user_id
                    ),
                    second_user_id=(
                        member_user_id
                    ),
                )
            )

            if not allowed:
                raise ChatPermissionError(
                    "All initial group members "
                    "must be accepted friends."
                )

        conversation = (
            await self.repository.create_group(
                self.session,
                creator_user_id=(
                    current_user_id
                ),
                name=name,
            )
        )

        await self.repository.add_member(
            self.session,
            conversation_id=conversation.id,
            user_id=current_user_id,
            role=ConversationMemberRole.OWNER,
        )

        for member_user_id in unique_members:
            await self.repository.add_member(
                self.session,
                conversation_id=conversation.id,
                user_id=member_user_id,
                role=(
                    ConversationMemberRole.MEMBER
                ),
            )

        return conversation

    async def list_conversations(
        self,
        *,
        user_id: uuid.UUID,
    ) -> list[Conversation]:
        return (
            await self.repository
            .list_conversations_for_user(
                self.session,
                user_id=user_id,
            )
        )

    async def add_group_member(
        self,
        *,
        conversation_id: uuid.UUID,
        current_user_id: uuid.UUID,
        target_user_id: uuid.UUID,
    ) -> ConversationMember:
        conversation = (
            await self._require_conversation(
                conversation_id
            )
        )

        if (
            conversation.conversation_type
            != ConversationType.GROUP
        ):
            raise ChatConflictError(
                "Members can only be added "
                "to group conversations."
            )

        current_member = (
            await self._require_active_member(
                conversation_id,
                current_user_id,
            )
        )

        if current_member.role not in (
            ConversationMemberRole.OWNER,
            ConversationMemberRole.ADMIN,
        ):
            raise ChatPermissionError(
                "Only group owners or admins "
                "can add members."
            )

        if not await self.friendship_service.are_friends(
            first_user_id=current_user_id,
            second_user_id=target_user_id,
        ):
            raise ChatPermissionError(
                "New group member must be "
                "an accepted friend."
            )

        return await self.repository.add_member(
            self.session,
            conversation_id=conversation_id,
            user_id=target_user_id,
            role=ConversationMemberRole.MEMBER,
        )

    async def remove_group_member(
        self,
        *,
        conversation_id: uuid.UUID,
        current_user_id: uuid.UUID,
        target_user_id: uuid.UUID,
    ) -> None:
        conversation = (
            await self._require_conversation(
                conversation_id
            )
        )

        if (
            conversation.conversation_type
            != ConversationType.GROUP
        ):
            raise ChatConflictError(
                "Members can only be removed "
                "from group conversations."
            )

        current_member = (
            await self._require_active_member(
                conversation_id,
                current_user_id,
            )
        )

        target_member = (
            await self._require_active_member(
                conversation_id,
                target_user_id,
            )
        )

        if (
            target_member.role
            == ConversationMemberRole.OWNER
        ):
            raise ChatConflictError(
                "Group owner cannot be removed."
            )

        if (
            current_user_id
            != target_user_id
            and current_member.role
            not in (
                ConversationMemberRole.OWNER,
                ConversationMemberRole.ADMIN,
            )
        ):
            raise ChatPermissionError(
                "Only group owners or admins "
                "can remove other members."
            )

        target_member.left_at = (
            datetime.now(
                timezone.utc
            )
        )

        await self.session.flush()

    async def send_message(
        self,
        *,
        conversation_id: uuid.UUID,
        sender_user_id: uuid.UUID,
        content: str,
    ) -> ChatMessage:
        await self._require_conversation(
            conversation_id
        )

        await self._require_active_member(
            conversation_id,
            sender_user_id,
        )

        return await self.repository.create_message(
            self.session,
            conversation_id=conversation_id,
            sender_user_id=sender_user_id,
            content=content,
        )

    async def list_messages(
        self,
        *,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        limit: int = 50,
    ) -> list[ChatMessage]:
        await self._require_conversation(
            conversation_id
        )

        await self._require_active_member(
            conversation_id,
            user_id,
        )

        safe_limit = max(
            1,
            min(
                limit,
                100,
            ),
        )

        return await self.repository.list_messages(
            self.session,
            conversation_id=conversation_id,
            limit=safe_limit,
        )

    async def _require_conversation(
        self,
        conversation_id: uuid.UUID,
    ) -> Conversation:
        conversation = (
            await self.repository
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

        return conversation

    async def _require_active_member(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> ConversationMember:
        member = (
            await self.repository.get_member(
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

        return member


__all__ = [
    "ChatConflictError",
    "ChatError",
    "ChatPermissionError",
    "ChatService",
    "ConversationNotFoundError",
]