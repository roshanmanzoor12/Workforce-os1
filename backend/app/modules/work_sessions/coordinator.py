from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.activity.models import ActivityStateEvent
from app.modules.work_sessions.repository import WorkSessionRepository
from app.modules.work_sessions.schemas import (
    WorkSessionProcessingResult,
)
from app.modules.work_sessions.service import (
    WorkSessionService,
)


class WorkSessionActivityCoordinator:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self._session = session

        self._repository = (
            WorkSessionRepository(
                session
            )
        )

        self._service = (
            WorkSessionService(
                self._repository
            )
        )

    async def process(
        self,
        event: ActivityStateEvent,
    ) -> WorkSessionProcessingResult:
        """
        Process a persisted activity event into the current work session.

        Tenant routing has already happened before this class is constructed.
        The device never supplies or controls a tenant database name.
        """

        return await self._service.process_activity_event(
            event
        )


__all__ = [
    "WorkSessionActivityCoordinator",
]