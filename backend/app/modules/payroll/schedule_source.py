from __future__ import annotations

import uuid
from datetime import (
    date,
    timedelta,
)

from fastapi import (
    HTTPException,
    status,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.modules.payroll.source_schemas import (
    PayrollScheduleDaySource,
    PayrollScheduleSource,
)
from app.modules.shifts.holiday_context import (
    ShiftHolidayContextService,
)
from app.modules.shifts.service import (
    ShiftService,
)


class PayrollScheduleSourceService:
    """
    Resolve authoritative scheduled payable units.

    Payroll may only consume published working schedule.

    Holiday treatment is applied through the existing Shift holiday
    context so paid/unpaid holiday behavior remains centralized.
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

        self.shifts = ShiftService(
            session
        )

        self.holidays = (
            ShiftHolidayContextService(
                session
            )
        )

    async def resolve(
        self,
        *,
        employee_id: uuid.UUID,
        period_start: date,
        period_end: date,
    ) -> PayrollScheduleSource:
        current = period_start

        days: list[
            PayrollScheduleDaySource
        ] = []

        scheduled_total = 0
        payable_total = 0

        while current <= period_end:
            base_day = await (
                self.shifts
                .resolve_employee_day(
                    employee_id=(
                        employee_id
                    ),
                    on_date=current,
                )
            )

            # ------------------------------------------------
            # Payroll cannot silently consume draft schedule.
            # ------------------------------------------------

            if (
                base_day.is_working_day
                and not base_day.is_published
            ):
                raise HTTPException(
                    status_code=(
                        status.HTTP_409_CONFLICT
                    ),
                    detail=(
                        "Payroll requires a "
                        "published schedule for "
                        f"{current.isoformat()}."
                    ),
                )

            resolved_day = await (
                self.holidays.apply(
                    base_day
                )
            )

            scheduled = max(
                0,
                int(
                    resolved_day
                    .scheduled_minutes
                ),
            )

            payable = max(
                0,
                int(
                    resolved_day
                    .payable_minutes
                ),
            )

            days.append(
                PayrollScheduleDaySource(
                    schedule_date=current,
                    shift_id=(
                        resolved_day
                        .shift_id
                    ),
                    source=(
                        resolved_day.source
                    ),
                    scheduled_minutes=(
                        scheduled
                    ),
                    payable_minutes=(
                        payable
                    ),
                    is_working_day=(
                        resolved_day
                        .is_working_day
                    ),
                    is_published=(
                        resolved_day
                        .is_published
                    ),
                )
            )

            scheduled_total += scheduled
            payable_total += payable

            current += timedelta(
                days=1
            )

        return PayrollScheduleSource(
            employee_id=employee_id,
            period_start=period_start,
            period_end=period_end,
            scheduled_minutes=(
                scheduled_total
            ),
            payable_minutes=(
                payable_total
            ),
            days=days,
        )


__all__ = [
    "PayrollScheduleSourceService",
]