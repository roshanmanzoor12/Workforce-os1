from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from .message_pagination_service import (
    MessagePage,
    MessagePaginationService,
)


@dataclass(
    frozen=True,
    slots=True,
)
class RealtimeResumeResult:
    conversation_id: uuid.UUID
    page: MessagePage


class RealtimeResumeService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        pagination_service: (
            MessagePaginationService | None
        ) = None,
    ) -> None:
        self.session = session

        self.pagination_service = (
            pagination_service
            or MessagePaginationService(
                session
            )
        )

    async def resume_conversation(
        self,
        *,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        cursor: str | None,
        limit: int = 50,
    ) -> RealtimeResumeResult:
        page = (
            await self.pagination_service.list_resume_page(
                conversation_id=conversation_id,
                user_id=user_id,
                cursor=cursor,
                limit=limit,
            )
        )

        return RealtimeResumeResult(
            conversation_id=conversation_id,
            page=page,
        )


__all__ = [
    "RealtimeResumeResult",
    "RealtimeResumeService",
]