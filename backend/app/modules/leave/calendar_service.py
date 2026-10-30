from __future__ import annotations

import uuid
from datetime import (
    date,
    timedelta,
)
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.modules.shifts.publication_snapshot import (
    SchedulePublicationSnapshotService,
)


ZERO = Decimal("0")
ONE = Decimal("1")


class LeaveCalendarService:
    """
    Schedule-aware leave calendar service.

    Two contracts intentionally coexist:

    1. inclusive_calendar_days()
       Legacy/foundation pure calendar calculation.

    2. chargeable_days()
       Authoritative Phase 12.2 schedule-aware calculation.

    Leave request balance charging uses chargeable_days().
    The legacy helper remains available for compatibility and
    low-level calendar math tests.
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

        self.schedule = (
            SchedulePublicationSnapshotService(
                session
            )
        )

    # =====================================================
    # LEGACY / PURE CALENDAR RANGE
    # =====================================================

    @staticmethod
    def inclusive_calendar_days(
        *,
        start_date: date,
        end_date: date,
    ) -> Decimal:
        """
        Return inclusive raw calendar-day count.

        Example:
            Oct 1 -> Oct 1 = 1
            Oct 1 -> Oct 5 = 5

        This method does NOT account for:
            - working days
            - published shifts
            - holidays
            - schedule exceptions

        It is retained as a pure calendar utility.

        Actual leave balance charging uses chargeable_days().
        """

        if end_date < start_date:
            raise ValueError(
                "end_date cannot be "
                "before start_date."
            )

        days = (
            end_date
            - start_date
        ).days + 1

        return Decimal(
            days
        )

    # =====================================================
    # PURE SCHEDULE-DAY CLASSIFICATION
    # =====================================================

    @staticmethod
    def is_chargeable_schedule_day(
        schedule_day: Any,
    ) -> bool:
        """
        A day consumes leave balance only when:

            scheduled working day
            AND
            not a workspace holiday
        """

        is_working_day = bool(
            getattr(
                schedule_day,
                "is_working_day",
                False,
            )
        )

        is_holiday = bool(
            getattr(
                schedule_day,
                "is_holiday",
                False,
            )
        )

        return (
            is_working_day
            and not is_holiday
        )

    # =====================================================
    # AUTHORITATIVE SINGLE-DAY RESOLUTION
    # =====================================================

    async def is_chargeable_day(
        self,
        *,
        employee_id: uuid.UUID,
        leave_date: date,
    ) -> bool:
        schedule_day = await (
            self.schedule.resolve_day(
                employee_id=(
                    employee_id
                ),
                schedule_date=(
                    leave_date
                ),
            )
        )

        return (
            self.is_chargeable_schedule_day(
                schedule_day
            )
        )

    # =====================================================
    # AUTHORITATIVE RANGE RESOLUTION
    # =====================================================

    async def chargeable_days(
        self,
        *,
        employee_id: uuid.UUID,
        start_date: date,
        end_date: date,
    ) -> Decimal:
        """
        Calculate the number of leave-balance days that should
        actually be charged for an employee.

        Uses the Shift publication snapshot resolver so published
        schedule state remains authoritative.
        """

        if end_date < start_date:
            raise ValueError(
                "end_date cannot be "
                "before start_date."
            )

        current = start_date

        total = ZERO

        while current <= end_date:
            if await self.is_chargeable_day(
                employee_id=(
                    employee_id
                ),
                leave_date=current,
            ):
                total += ONE

            current += timedelta(
                days=1
            )

        return total


__all__ = [
    "LeaveCalendarService",
]