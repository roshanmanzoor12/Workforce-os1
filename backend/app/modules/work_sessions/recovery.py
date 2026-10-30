from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.work_sessions.repository import (
    WorkSessionRepository,
)
from app.modules.work_sessions.service import (
    WorkSessionService,
)


DEFAULT_STALE_SESSION_SECONDS = 10 * 60


class WorkSessionRecoveryService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        stale_session_seconds: int = (
            DEFAULT_STALE_SESSION_SECONDS
        ),
    ) -> None:
        if stale_session_seconds <= 0:
            raise ValueError(
                "stale_session_seconds must be greater than zero."
            )

        self._stale_session_seconds = (
            stale_session_seconds
        )

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

    async def close_stale(
        self,
        *,
        now: datetime | None = None,
        limit: int = 500,
    ) -> int:
        current_time = (
            now
            or datetime.now(
                timezone.utc
            )
        )

        if current_time.tzinfo is None:
            raise ValueError(
                "now must be timezone-aware."
            )

        cutoff = (
            current_time
            - timedelta(
                seconds=self._stale_session_seconds
            )
        )

        return await self._service.close_stale_sessions(
            stale_before=cutoff,
            limit=limit,
        )


__all__ = [
    "DEFAULT_STALE_SESSION_SECONDS",
    "WorkSessionRecoveryService",
]