from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.activity.models import ActivityStateEvent
from app.modules.work_sessions.coordinator import (
    WorkSessionActivityCoordinator,
)
from app.modules.work_sessions.schemas import (
    WorkSessionProcessingResult,
)


async def on_activity_state_event(
    session: AsyncSession,
    event: ActivityStateEvent,
) -> WorkSessionProcessingResult:
    coordinator = (
        WorkSessionActivityCoordinator(
            session
        )
    )

    return await coordinator.process(
        event
    )


__all__ = [
    "on_activity_state_event",
]