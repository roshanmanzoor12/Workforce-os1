from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.app_tracking.models import (
    APP_USAGE_STATUS_OPEN,
    AppObservation,
    AppUsageInterval,
)


class AppTrackingQueryService:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self._session = session

    async def get_latest_observation(
        self,
        device_id: UUID,
    ) -> AppObservation | None:
        statement = (
            select(
                AppObservation
            )
            .where(
                AppObservation.device_id
                == device_id
            )
            .order_by(
                AppObservation.observed_at.desc(),
                AppObservation.id.desc(),
            )
            .limit(1)
        )

        result = await self._session.execute(
            statement
        )

        return result.scalar_one_or_none()

    async def get_current_interval(
        self,
        device_id: UUID,
    ) -> AppUsageInterval | None:
        statement = (
            select(
                AppUsageInterval
            )
            .where(
                AppUsageInterval.device_id
                == device_id,
                AppUsageInterval.status
                == APP_USAGE_STATUS_OPEN,
            )
            .order_by(
                AppUsageInterval.started_at.desc()
            )
            .limit(1)
        )

        result = await self._session.execute(
            statement
        )

        return result.scalar_one_or_none()


__all__ = [
    "AppTrackingQueryService",
]