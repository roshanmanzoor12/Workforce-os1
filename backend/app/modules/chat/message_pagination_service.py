from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from .message_query_repository import MessageQueryRepository
from .models import ChatMessage
from .pagination import decode_message_cursor, encode_message_cursor
from .repository import ChatRepository
from .service import ChatPermissionError, ConversationNotFoundError


@dataclass(frozen=True, slots=True)
class MessagePage:
    items: list[ChatMessage]
    next_cursor: str | None
    has_more: bool


class MessagePaginationService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        repository: MessageQueryRepository | None = None,
        chat_repository: ChatRepository | None = None,
    ) -> None:
        self.session = session
        self.repository = repository or MessageQueryRepository()
        self.chat_repository = chat_repository or ChatRepository()

    async def list_page(
        self,
        *,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        limit: int = 50,
        cursor: str | None = None,
    ) -> MessagePage:
        await self._require_active_member(
            conversation_id=conversation_id,
            user_id=user_id,
        )

        safe_limit = max(1, min(int(limit), 100))

        decoded_cursor = (
            decode_message_cursor(cursor)
            if cursor is not None
            else None
        )

        rows = await self.repository.list_page(
            self.session,
            conversation_id=conversation_id,
            limit=safe_limit,
            cursor=decoded_cursor,
        )

        has_more = len(rows) > safe_limit
        items = rows[:safe_limit]
        next_cursor = None

        if has_more and items:
            last_item = items[-1]

            next_cursor = encode_message_cursor(
                created_at=last_item.created_at,
                message_id=last_item.id,
            )

        return MessagePage(
            items=items,
            next_cursor=next_cursor,
            has_more=has_more,
        )

    async def list_resume_page(
        self,
        *,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        limit: int = 50,
        cursor: str | None = None,
    ) -> MessagePage:
        await self._require_active_member(
            conversation_id=conversation_id,
            user_id=user_id,
        )

        safe_limit = max(1, min(int(limit), 100))

        if cursor is None:
            # Bootstrap the latest visible messages and a forward watermark.
            # Older history remains available through list_page().
            rows = await self.repository.list_page(
                self.session,
                conversation_id=conversation_id,
                limit=safe_limit,
                cursor=None,
            )

            items = list(reversed(rows[:safe_limit]))
            has_more = False

        else:
            decoded_cursor = decode_message_cursor(cursor)

            if not await self.repository.cursor_exists(
                self.session,
                conversation_id=conversation_id,
                cursor=decoded_cursor,
            ):
                raise ValueError(
                    "Resume cursor does not identify a message "
                    "in this conversation. Fetch a fresh snapshot."
                )

            rows = await self.repository.list_after_page(
                self.session,
                conversation_id=conversation_id,
                limit=safe_limit,
                cursor=decoded_cursor,
            )

            has_more = len(rows) > safe_limit
            items = rows[:safe_limit]

        # Unlike history, keep the watermark even after catching up.
        next_cursor = cursor

        if items:
            last_item = items[-1]

            next_cursor = encode_message_cursor(
                created_at=last_item.created_at,
                message_id=last_item.id,
            )

        return MessagePage(
            items=items,
            next_cursor=next_cursor,
            has_more=has_more,
        )

    async def _require_active_member(
        self,
        *,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        conversation = await self.chat_repository.get_conversation(
            self.session,
            conversation_id=conversation_id,
        )

        if conversation is None or not conversation.is_active:
            raise ConversationNotFoundError(
                "Conversation not found."
            )

        member = await self.chat_repository.get_member(
            self.session,
            conversation_id=conversation_id,
            user_id=user_id,
        )

        if member is None or member.left_at is not None:
            raise ChatPermissionError(
                "User is not an active member of this conversation."
            )


__all__ = [
    "MessagePage",
    "MessagePaginationService",
]