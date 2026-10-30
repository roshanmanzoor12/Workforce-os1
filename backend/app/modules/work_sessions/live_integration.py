from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.activity.models import (
    ActivityStateEvent,
)
from app.modules.work_sessions.activity_hook import (
    on_activity_state_event,
)
from app.modules.work_sessions.schemas import (
    WorkSessionProcessingResult,
)


async def process_persisted_activity_event(
    session: AsyncSession,
    event_id: UUID,
) -> WorkSessionProcessingResult:
    """
    Load one already-persisted activity event from the current tenant
    database and apply it to the corresponding work session.

    Tenant routing has already happened before this function is called.
    """

    statement = (
        select(
            ActivityStateEvent
        )
        .where(
            ActivityStateEvent.id == event_id
        )
        .limit(1)
    )

    result = await session.execute(
        statement
    )

    event = (
        result.scalar_one_or_none()
    )

    if event is None:
        raise RuntimeError(
            f"Activity event not found: {event_id}"
        )

    return await on_activity_state_event(
        session,
        event,
    )


__all__ = [
    "process_persisted_activity_event",
]