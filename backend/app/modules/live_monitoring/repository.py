from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    func,
    select,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.modules.live_monitoring.models import (
    LiveScreenSession,
    ScreenshotCaptureRequest,
)


class LiveMonitoringRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def create_screenshot(
        self,
        item: ScreenshotCaptureRequest,
    ) -> ScreenshotCaptureRequest:
        self.session.add(
            item
        )

        await self.session.flush()

        await self.session.refresh(
            item
        )

        return item

    async def get_screenshot(
        self,
        *,
        request_id: uuid.UUID,
    ) -> ScreenshotCaptureRequest | None:
        result = await self.session.execute(
            select(
                ScreenshotCaptureRequest
            ).where(
                ScreenshotCaptureRequest.id
                == request_id
            )
        )

        return (
            result
            .scalar_one_or_none()
        )

    async def list_screenshots(
        self,
        *,
        employee_ids: (
            frozenset[
                uuid.UUID
            ]
            | None
        ),
        limit: int,
        offset: int,
    ) -> tuple[
        list[
            ScreenshotCaptureRequest
        ],
        int,
    ]:
        filters = []

        if employee_ids is not None:
            if not employee_ids:
                return (
                    [],
                    0,
                )

            filters.append(
                ScreenshotCaptureRequest
                .employee_id
                .in_(
                    tuple(
                        employee_ids
                    )
                )
            )

        count_statement = select(
            func.count(
                ScreenshotCaptureRequest.id
            )
        )

        if filters:
            count_statement = (
                count_statement.where(
                    *filters
                )
            )

        total_result = await (
            self.session.execute(
                count_statement
            )
        )

        total = int(
            total_result.scalar_one()
        )

        statement = (
            select(
                ScreenshotCaptureRequest
            )
            .order_by(
                ScreenshotCaptureRequest
                .requested_at
                .desc()
            )
            .limit(
                limit
            )
            .offset(
                offset
            )
        )

        if filters:
            statement = statement.where(
                *filters
            )

        result = await self.session.execute(
            statement
        )

        return (
            list(
                result
                .scalars()
                .all()
            ),
            total,
        )

    async def list_screenshots_filtered(
        self,
        *,
        employee_ids: (
            frozenset[
                uuid.UUID
            ]
            | None
        ),
        employee_id: uuid.UUID | None,
        device_id: uuid.UUID | None,
        status: str | None,
        start_at: datetime | None,
        end_at: datetime | None,
        limit: int,
        offset: int,
    ) -> tuple[
        list[
            ScreenshotCaptureRequest
        ],
        int,
    ]:
        filters = []

        if employee_id is not None:
            if (
                employee_ids is not None
                and employee_id
                not in employee_ids
            ):
                return (
                    [],
                    0,
                )

            filters.append(
                ScreenshotCaptureRequest
                .employee_id
                == employee_id
            )

        elif employee_ids is not None:
            if not employee_ids:
                return (
                    [],
                    0,
                )

            filters.append(
                ScreenshotCaptureRequest
                .employee_id
                .in_(
                    tuple(
                        employee_ids
                    )
                )
            )

        if device_id is not None:
            filters.append(
                ScreenshotCaptureRequest
                .device_id
                == device_id
            )

        if status is not None:
            filters.append(
                ScreenshotCaptureRequest
                .status
                == status
            )

        if start_at is not None:
            filters.append(
                ScreenshotCaptureRequest
                .requested_at
                >= start_at
            )

        if end_at is not None:
            filters.append(
                ScreenshotCaptureRequest
                .requested_at
                < end_at
            )

        count_statement = (
            select(
                func.count(
                    ScreenshotCaptureRequest.id
                )
            )
        )

        if filters:
            count_statement = (
                count_statement.where(
                    *filters
                )
            )

        total_result = await (
            self.session.execute(
                count_statement
            )
        )

        total = int(
            total_result.scalar_one()
            or 0
        )

        statement = (
            select(
                ScreenshotCaptureRequest
            )
            .order_by(
                ScreenshotCaptureRequest
                .requested_at
                .desc(),
                ScreenshotCaptureRequest
                .id
                .desc(),
            )
            .limit(
                limit
            )
            .offset(
                offset
            )
        )

        if filters:
            statement = statement.where(
                *filters
            )

        result = await (
            self.session.execute(
                statement
            )
        )

        return (
            list(
                result.scalars().all()
            ),
            total,
        )

    async def create_live_session(
        self,
        item: LiveScreenSession,
    ) -> LiveScreenSession:
        self.session.add(
            item
        )

        await self.session.flush()

        await self.session.refresh(
            item
        )

        return item

    async def get_live_session(
        self,
        *,
        session_id: uuid.UUID,
    ) -> LiveScreenSession | None:
        result = await self.session.execute(
            select(
                LiveScreenSession
            ).where(
                LiveScreenSession.id
                == session_id
            )
        )

        return (
            result
            .scalar_one_or_none()
        )

    async def refresh_screenshot(
        self,
        item: ScreenshotCaptureRequest,
    ) -> ScreenshotCaptureRequest:
        await self.session.flush()

        await self.session.refresh(
            item
        )

        return item

    async def refresh_live_session(
        self,
        item: LiveScreenSession,
    ) -> LiveScreenSession:
        await self.session.flush()

        await self.session.refresh(
            item
        )

        return item


__all__ = [
    "LiveMonitoringRepository",
]