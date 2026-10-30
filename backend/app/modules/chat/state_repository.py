from __future__ import annotations

import uuid
from datetime import (
    datetime,
    timezone,
)

from sqlalchemy import (
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession

from .models import (
    ChatMessage,
    ChatMessageReceipt,
    ChatPresence,
)


class ChatStateRepository:
    async def get_message(
        self,
        session: AsyncSession,
        *,
        message_id: uuid.UUID,
    ) -> ChatMessage | None:
        result = await session.execute(
            select(
                ChatMessage
            ).where(
                ChatMessage.id
                == message_id
            )
        )

        return result.scalar_one_or_none()

    async def save_receipt(
        self,
        session: AsyncSession,
        *,
        message_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> ChatMessageReceipt:
        result = await session.execute(
            select(
                ChatMessageReceipt
            ).where(
                ChatMessageReceipt.message_id
                == message_id,
                ChatMessageReceipt.user_id
                == user_id,
            )
        )

        receipt = result.scalar_one_or_none()

        if receipt is not None:
            receipt.read_at = datetime.now(
                timezone.utc
            )

            await session.flush()

            return receipt

        receipt = ChatMessageReceipt(
            message_id=message_id,
            user_id=user_id,
        )

        session.add(
            receipt
        )

        await session.flush()

        return receipt

    async def list_receipts(
        self,
        session: AsyncSession,
        *,
        message_id: uuid.UUID,
    ) -> list[ChatMessageReceipt]:
        result = await session.execute(
            select(
                ChatMessageReceipt
            )
            .where(
                ChatMessageReceipt.message_id
                == message_id
            )
            .order_by(
                ChatMessageReceipt.read_at.asc()
            )
        )

        return list(
            result.scalars().all()
        )

    async def get_presence(
        self,
        session: AsyncSession,
        *,
        user_id: uuid.UUID,
    ) -> ChatPresence | None:
        result = await session.execute(
            select(
                ChatPresence
            ).where(
                ChatPresence.user_id
                == user_id
            )
        )

        return result.scalar_one_or_none()

    async def ensure_presence(
        self,
        session: AsyncSession,
        *,
        user_id: uuid.UUID,
    ) -> ChatPresence:
        presence = await self.get_presence(
            session,
            user_id=user_id,
        )

        if presence is not None:
            return presence

        presence = ChatPresence(
            user_id=user_id,
        )

        session.add(
            presence
        )

        await session.flush()

        return presence


__all__ = [
    "ChatStateRepository",
]