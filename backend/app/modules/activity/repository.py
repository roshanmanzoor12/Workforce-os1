from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.activity.models import ActivityStateEvent


__all__ = [
    "ActivityRepository",
]


class ActivityRepository:
    """
    Tenant-local repository for active/idle state events.

    This repository never resolves workspace routing itself.
    It receives an already-routed tenant AsyncSession.
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    # =========================================================
    # CREATE
    # =========================================================

    async def create_event(
        self,
        *,
        device_id: uuid.UUID,
        employee_id: uuid.UUID | None,
        state: str,
        idle_seconds: int,
        last_input_at: datetime | None,
        observed_at: datetime,
        received_at: datetime,
    ) -> ActivityStateEvent:
        event = ActivityStateEvent(
            device_id=device_id,
            employee_id=employee_id,
            state=state,
            idle_seconds=idle_seconds,
            last_input_at=last_input_at,
            observed_at=observed_at,
            received_at=received_at,
            created_at=received_at,
        )

        self.session.add(
            event
        )

        await self.session.flush()

        return event

    # =========================================================
    # LATEST BY DEVICE
    # =========================================================

    async def get_latest_for_device(
        self,
        *,
        device_id: uuid.UUID,
    ) -> ActivityStateEvent | None:
        statement = (
            select(
                ActivityStateEvent
            )
            .where(
                ActivityStateEvent.device_id
                == device_id
            )
            .order_by(
                desc(
                    ActivityStateEvent.observed_at
                ),
                desc(
                    ActivityStateEvent.received_at
                ),
            )
            .limit(
                1
            )
        )

        result = await self.session.execute(
            statement
        )

        return result.scalar_one_or_none()

    # =========================================================
    # LATEST BY EMPLOYEE
    # =========================================================

    async def get_latest_for_employee(
        self,
        *,
        employee_id: uuid.UUID,
    ) -> ActivityStateEvent | None:
        statement = (
            select(
                ActivityStateEvent
            )
            .where(
                ActivityStateEvent.employee_id
                == employee_id
            )
            .order_by(
                desc(
                    ActivityStateEvent.observed_at
                ),
                desc(
                    ActivityStateEvent.received_at
                ),
            )
            .limit(
                1
            )
        )

        result = await self.session.execute(
            statement
        )

        return result.scalar_one_or_none()

    # =========================================================
    # DEVICE HISTORY
    # =========================================================

    async def list_for_device(
        self,
        *,
        device_id: uuid.UUID,
        limit: int = 100,
    ) -> Sequence[ActivityStateEvent]:
        safe_limit = max(
            1,
            min(
                limit,
                500,
            ),
        )

        statement = (
            select(
                ActivityStateEvent
            )
            .where(
                ActivityStateEvent.device_id
                == device_id
            )
            .order_by(
                desc(
                    ActivityStateEvent.observed_at
                ),
                desc(
                    ActivityStateEvent.received_at
                ),
            )
            .limit(
                safe_limit
            )
        )

        result = await self.session.execute(
            statement
        )

        return result.scalars().all()

    # =========================================================
    # EMPLOYEE HISTORY
    # =========================================================

    async def list_for_employee(
        self,
        *,
        employee_id: uuid.UUID,
        limit: int = 100,
    ) -> Sequence[ActivityStateEvent]:
        safe_limit = max(
            1,
            min(
                limit,
                500,
            ),
        )

        statement = (
            select(
                ActivityStateEvent
            )
            .where(
                ActivityStateEvent.employee_id
                == employee_id
            )
            .order_by(
                desc(
                    ActivityStateEvent.observed_at
                ),
                desc(
                    ActivityStateEvent.received_at
                ),
            )
            .limit(
                safe_limit
            )
        )

        result = await self.session.execute(
            statement
        )

        return result.scalars().all()

    # =========================================================
    # TIME RANGE
    # =========================================================

    async def list_device_events_between(
        self,
        *,
        device_id: uuid.UUID,
        start_at: datetime,
        end_at: datetime,
        limit: int = 500,
    ) -> Sequence[ActivityStateEvent]:
        safe_limit = max(
            1,
            min(
                limit,
                2_000,
            ),
        )

        statement = (
            select(
                ActivityStateEvent
            )
            .where(
                ActivityStateEvent.device_id
                == device_id,
                ActivityStateEvent.observed_at
                >= start_at,
                ActivityStateEvent.observed_at
                <= end_at,
            )
            .order_by(
                ActivityStateEvent.observed_at.asc(),
                ActivityStateEvent.received_at.asc(),
            )
            .limit(
                safe_limit
            )
        )

        result = await self.session.execute(
            statement
        )

        return result.scalars().all()

    # =========================================================
    # COMMIT HELPERS
    # =========================================================

    async def commit(
        self,
    ) -> None:
        await self.session.commit()

    async def rollback(
        self,
    ) -> None:
        await self.session.rollback()

    async def refresh(
        self,
        event: ActivityStateEvent,
    ) -> ActivityStateEvent:
        await self.session.refresh(
            event
        )

        return event