from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.activity.models import (
    ActivityStateEvent,
)
from app.modules.work_sessions.activity_hook import (
    on_activity_state_event,
)


class WorkSessionReconciliationService:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self._session = session

    async def reconcile_device(
        self,
        device_id: UUID,
        *,
        observed_from: datetime | None = None,
        limit: int = 5000,
    ) -> int:
        if limit <= 0:
            raise ValueError(
                "limit must be greater than zero."
            )

        statement = (
            select(
                ActivityStateEvent
            )
            .where(
                ActivityStateEvent.device_id == device_id
            )
        )

        if observed_from is not None:
            if observed_from.tzinfo is None:
                raise ValueError(
                    "observed_from must be timezone-aware."
                )

            statement = statement.where(
                ActivityStateEvent.observed_at
                >= observed_from
            )

        statement = (
            statement
            .order_by(
                ActivityStateEvent.observed_at.asc(),
                ActivityStateEvent.id.asc(),
            )
            .limit(
                limit
            )
        )

        result = await self._session.execute(
            statement
        )

        events = list(
            result.scalars().all()
        )

        processed_count = 0

        for event in events:
            processing_result = (
                await on_activity_state_event(
                    self._session,
                    event,
                )
            )

            if not processing_result.ignored_event:
                processed_count += 1

        return processed_count


__all__ = [
    "WorkSessionReconciliationService",
]