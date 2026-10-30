from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import (
    Conversation,
    ConversationMember,
)


class RealtimeRecipientRepository:
    async def list_active_user_ids(
        self,
        session: AsyncSession,
        *,
        conversation_id: uuid.UUID,
    ) -> list[uuid.UUID]:
        result = await session.execute(
            select(ConversationMember.user_id)
            .join(
                Conversation,
                Conversation.id
                == ConversationMember.conversation_id,
            )
            .where(
                ConversationMember.conversation_id
                == conversation_id,
                ConversationMember.left_at.is_(None),
                Conversation.is_active.is_(True),
            )
            .distinct()
            .order_by(ConversationMember.user_id)
        )

        return list(
            result.scalars().all()
        )


__all__ = [
    "RealtimeRecipientRepository",
]