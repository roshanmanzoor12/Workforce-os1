from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import (
    select,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.modules.holidays.models import (
    Holiday,
)


class HolidayRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    # =====================================================
    # LIST
    # =====================================================

    async def list(
        self,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
        active_only: bool = False,
    ) -> list[Holiday]:
        statement = select(
            Holiday
        )

        if start_date is not None:
            statement = statement.where(
                Holiday.holiday_date
                >= start_date
            )

        if end_date is not None:
            statement = statement.where(
                Holiday.holiday_date
                <= end_date
            )

        if active_only:
            statement = statement.where(
                Holiday.is_active.is_(
                    True
                )
            )

        statement = statement.order_by(
            Holiday.holiday_date.asc(),
            Holiday.name.asc(),
        )

        result = await self.session.scalars(
            statement
        )

        return list(result)

    # =====================================================
    # GET
    # =====================================================

    async def get(
        self,
        *,
        holiday_id: uuid.UUID,
    ) -> Holiday | None:
        return await self.session.scalar(
            select(
                Holiday
            ).where(
                Holiday.id
                == holiday_id
            )
        )

    # =====================================================
    # DATE RESOLUTION
    # =====================================================

    async def for_date(
        self,
        *,
        holiday_date: date,
    ) -> Holiday | None:
        """
        Generic active holiday lookup.

        This may return either:

        - workspace-wide holiday
        - regional holiday

        Employee schedule resolution should normally use
        workspace_for_date() unless an employee-region mapping
        exists.
        """

        return await self.session.scalar(
            select(
                Holiday
            )
            .where(
                Holiday.holiday_date
                == holiday_date,
                Holiday.is_active.is_(
                    True
                ),
            )
            .order_by(
                Holiday.name.asc()
            )
        )

    async def workspace_for_date(
        self,
        *,
        holiday_date: date,
    ) -> Holiday | None:
        """
        Resolve a workspace-wide holiday.

        A holiday is workspace-wide when region IS NULL.

        Regional holidays must not be applied to every employee
        until WorkforceOS has an explicit employee/location/region
        mapping.
        """

        return await self.session.scalar(
            select(
                Holiday
            )
            .where(
                Holiday.holiday_date
                == holiday_date,
                Holiday.is_active.is_(
                    True
                ),
                Holiday.region.is_(
                    None
                ),
            )
            .order_by(
                Holiday.name.asc()
            )
        )


__all__ = [
    "HolidayRepository",
]