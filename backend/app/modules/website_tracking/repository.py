from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Select,
    select,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.modules.website_tracking.models import (
    WEBSITE_USAGE_STATUS_OPEN,
    WebsiteObservation,
    WebsiteUsageInterval,
)


class WebsiteTrackingRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self._session = session

    async def create_observation(
        self,
        *,
        device_id: uuid.UUID,
        employee_id: uuid.UUID | None,
        browser_name: str,
        browser_process_name: str,
        domain: str,
        normalized_domain: str,
        page_url: str | None,
        page_title: str | None,
        observed_at: datetime,
    ) -> WebsiteObservation:
        observation = WebsiteObservation(
            device_id=device_id,
            employee_id=employee_id,
            browser_name=browser_name,
            browser_process_name=browser_process_name,
            domain=domain,
            normalized_domain=normalized_domain,
            page_url=page_url,
            page_title=page_title,
            observed_at=observed_at,
        )

        self._session.add(
            observation
        )

        await self._session.flush()

        return observation

    async def create_interval(
        self,
        *,
        device_id: uuid.UUID,
        employee_id: uuid.UUID | None,
        browser_name: str,
        browser_process_name: str,
        domain: str,
        normalized_domain: str,
        started_at: datetime,
        page_url: str | None,
        page_title: str | None,
    ) -> WebsiteUsageInterval:
        interval = WebsiteUsageInterval(
            device_id=device_id,
            employee_id=employee_id,
            browser_name=browser_name,
            browser_process_name=browser_process_name,
            domain=domain,
            normalized_domain=normalized_domain,
            status=WEBSITE_USAGE_STATUS_OPEN,
            started_at=started_at,
            ended_at=None,
            last_observed_at=started_at,
            duration_seconds=0,
            last_page_url=page_url,
            last_page_title=page_title,
        )

        self._session.add(
            interval
        )

        await self._session.flush()

        return interval

    async def get_open_interval(
        self,
        *,
        device_id: uuid.UUID,
        for_update: bool = False,
    ) -> WebsiteUsageInterval | None:
        statement: Select[
            tuple[
                WebsiteUsageInterval
            ]
        ] = (
            select(
                WebsiteUsageInterval
            )
            .where(
                WebsiteUsageInterval.device_id
                == device_id,
                WebsiteUsageInterval.status
                == WEBSITE_USAGE_STATUS_OPEN,
            )
            .order_by(
                WebsiteUsageInterval.started_at.desc()
            )
            .limit(
                1
            )
        )

        if for_update:
            statement = statement.with_for_update()

        result = await self._session.execute(
            statement
        )

        return result.scalar_one_or_none()

    async def get_latest_observation(
        self,
        *,
        device_id: uuid.UUID,
    ) -> WebsiteObservation | None:
        result = await self._session.execute(
            select(
                WebsiteObservation
            )
            .where(
                WebsiteObservation.device_id
                == device_id
            )
            .order_by(
                WebsiteObservation.observed_at.desc()
            )
            .limit(
                1
            )
        )

        return result.scalar_one_or_none()

    async def list_device_intervals(
        self,
        *,
        device_id: uuid.UUID,
        limit: int = 100,
    ) -> list[
        WebsiteUsageInterval
    ]:
        result = await self._session.execute(
            select(
                WebsiteUsageInterval
            )
            .where(
                WebsiteUsageInterval.device_id
                == device_id
            )
            .order_by(
                WebsiteUsageInterval.started_at.desc()
            )
            .limit(
                limit
            )
        )

        return list(
            result.scalars().all()
        )

    async def list_employee_intervals(
        self,
        *,
        employee_id: uuid.UUID,
        limit: int = 100,
    ) -> list[
        WebsiteUsageInterval
    ]:
        result = await self._session.execute(
            select(
                WebsiteUsageInterval
            )
            .where(
                WebsiteUsageInterval.employee_id
                == employee_id
            )
            .order_by(
                WebsiteUsageInterval.started_at.desc()
            )
            .limit(
                limit
            )
        )

        return list(
            result.scalars().all()
        )

    async def list_intervals_between(
        self,
        *,
        device_id: uuid.UUID,
        start_at: datetime,
        end_at: datetime,
    ) -> list[
        WebsiteUsageInterval
    ]:
        result = await self._session.execute(
            select(
                WebsiteUsageInterval
            )
            .where(
                WebsiteUsageInterval.device_id
                == device_id,
                WebsiteUsageInterval.started_at
                < end_at,
                WebsiteUsageInterval.last_observed_at
                >= start_at,
            )
            .order_by(
                WebsiteUsageInterval.started_at.asc()
            )
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
        entity: object,
    ) -> None:
        await self._session.refresh(
            entity
        )


__all__ = [
    "WebsiteTrackingRepository",
]