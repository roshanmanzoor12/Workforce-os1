from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.app_tracking.models import (
    APP_USAGE_STATUS_OPEN,
    AppObservation,
    AppUsageInterval,
)


class AppTrackingRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self._session = session

    async def create_observation(
        self,
        observation: AppObservation,
    ) -> AppObservation:
        self._session.add(
            observation
        )

        await self._session.flush()

        return observation

    async def create_interval(
        self,
        interval: AppUsageInterval,
    ) -> AppUsageInterval:
        self._session.add(
            interval
        )

        await self._session.flush()

        return interval

    async def get_open_interval_for_device(
        self,
        device_id: UUID,
    ) -> AppUsageInterval | None:
        statement = (
            select(
                AppUsageInterval
            )
            .where(
                AppUsageInterval.device_id == device_id,
                AppUsageInterval.status == APP_USAGE_STATUS_OPEN,
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

    async def list_intervals_for_device(
        self,
        device_id: UUID,
        *,
        limit: int = 200,
    ) -> list[AppUsageInterval]:
        statement = (
            select(
                AppUsageInterval
            )
            .where(
                AppUsageInterval.device_id == device_id
            )
            .order_by(
                AppUsageInterval.started_at.desc()
            )
            .limit(limit)
        )

        result = await self._session.execute(
            statement
        )

        return list(
            result.scalars().all()
        )

    async def list_intervals_for_employee(
        self,
        employee_id: UUID,
        *,
        limit: int = 200,
    ) -> list[AppUsageInterval]:
        statement = (
            select(
                AppUsageInterval
            )
            .where(
                AppUsageInterval.employee_id == employee_id
            )
            .order_by(
                AppUsageInterval.started_at.desc()
            )
            .limit(limit)
        )

        result = await self._session.execute(
            statement
        )

        return list(
            result.scalars().all()
        )

    async def list_intervals_between(
        self,
        *,
        started_from: datetime,
        started_to: datetime,
        employee_id: UUID | None = None,
        device_id: UUID | None = None,
        limit: int = 5000,
    ) -> list[AppUsageInterval]:
        statement = (
            select(
                AppUsageInterval
            )
            .where(
                AppUsageInterval.started_at >= started_from,
                AppUsageInterval.started_at < started_to,
            )
        )

        if employee_id is not None:
            statement = statement.where(
                AppUsageInterval.employee_id == employee_id
            )

        if device_id is not None:
            statement = statement.where(
                AppUsageInterval.device_id == device_id
            )

        statement = (
            statement
            .order_by(
                AppUsageInterval.started_at.asc()
            )
            .limit(limit)
        )

        result = await self._session.execute(
            statement
        )

        return list(
            result.scalars().all()
        )

    async def commit(
        self,
    ) -> None:
        await self._session.commit()

    async def rollback(
        self,
    ) -> None:
        await self._session.rollback()

    async def refresh(
        self,
        instance: AppObservation | AppUsageInterval,
    ) -> None:
        await self._session.refresh(
            instance
        )


__all__ = [
    "AppTrackingRepository",
]