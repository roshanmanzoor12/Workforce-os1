from __future__ import annotations

import uuid

from sqlalchemy import (
    and_,
    or_,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession

from .models import (
    ChatMessage,
)
from .pagination import (
    MessageCursor,
)


class MessageQueryRepository:
    async def list_page(
        self,
        session: AsyncSession,
        *,
        conversation_id: uuid.UUID,
        limit: int,
        cursor: MessageCursor | None = None,
    ) -> list[ChatMessage]:
        safe_limit = max(
            1,
            min(
                int(limit),
                100,
            ),
        )

        statement = (
            select(ChatMessage)
            .where(
                ChatMessage.conversation_id
                == conversation_id,
                ChatMessage.deleted_at.is_(None),
            )
        )

        if cursor is not None:
            statement = statement.where(
                or_(
                    ChatMessage.created_at
                    < cursor.created_at,
                    and_(
                        ChatMessage.created_at
                        == cursor.created_at,
                        ChatMessage.id
                        < cursor.message_id,
                    ),
                )
            )

        statement = (
            statement
            .order_by(
                ChatMessage.created_at.desc(),
                ChatMessage.id.desc(),
            )
            .limit(safe_limit + 1)
        )

        result = await session.execute(
            statement
        )

        return list(
            result.scalars().all()
        )

    async def cursor_exists(
        self,
        session: AsyncSession,
        *,
        conversation_id: uuid.UUID,
        cursor: MessageCursor,
    ) -> bool:
        """
        Validate a recovery anchor against its conversation.

        Soft-deleted messages remain valid anchors because
        deletion does not change their creation position.
        """

        statement = (
            select(ChatMessage.id)
            .where(
                ChatMessage.conversation_id
                == conversation_id,
                ChatMessage.id
                == cursor.message_id,
                ChatMessage.created_at
                == cursor.created_at,
            )
            .limit(1)
        )

        message_id = await session.scalar(
            statement
        )

        return message_id is not None

    async def list_after_page(
        self,
        session: AsyncSession,
        *,
        conversation_id: uuid.UUID,
        limit: int,
        cursor: MessageCursor,
    ) -> list[ChatMessage]:
        """
        Fetch visible messages after a validated anchor.

        Timestamp and UUID together provide a stable order
        when multiple messages share a creation timestamp.
        """

        safe_limit = max(
            1,
            min(
                int(limit),
                100,
            ),
        )

        statement = (
            select(ChatMessage)
            .where(
                ChatMessage.conversation_id
                == conversation_id,
                ChatMessage.deleted_at.is_(None),
                or_(
                    ChatMessage.created_at
                    > cursor.created_at,
                    and_(
                        ChatMessage.created_at
                        == cursor.created_at,
                        ChatMessage.id
                        > cursor.message_id,
                    ),
                ),
            )
            .order_by(
                ChatMessage.created_at.asc(),
                ChatMessage.id.asc(),
            )
            .limit(safe_limit + 1)
        )

        result = await session.execute(
            statement
        )

        return list(
            result.scalars().all()
        )


__all__ = [
    "MessageQueryRepository",
]