from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.activity.models import ActivityStateEvent
from app.modules.work_sessions.repository import WorkSessionRepository
from app.modules.work_sessions.schemas import WorkSessionProcessingResult
from app.modules.work_sessions.service import WorkSessionService


async def process_activity_event_into_work_session(
    session: AsyncSession,
    event: ActivityStateEvent,
) -> WorkSessionProcessingResult:
    """
    Convert one persisted activity observation into work-session state.

    This function intentionally accepts the existing tenant AsyncSession so
    activity persistence and work-session processing remain inside the same
    tenant database plane.

    The Windows agent never selects or accesses a tenant database directly.
    """

    repository = WorkSessionRepository(
        session
    )

    service = WorkSessionService(
        repository
    )

    return await service.process_activity_event(
        event
    )


__all__ = [
    "process_activity_event_into_work_session",
]