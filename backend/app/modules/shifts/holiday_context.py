from __future__ import annotations

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.modules.holidays.service import (
    HolidayService,
)
from app.modules.shifts.schemas import (
    ResolvedScheduleDayResponse,
)


class ShiftHolidayContextService:
    """
    Adds holiday metadata to a resolved schedule day.

    It deliberately does NOT change payable_minutes.

    Payability of paid/unpaid holidays belongs to payroll/
    compensation policy, not scheduling.
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.holidays = (
            HolidayService(
                session
            )
        )

    async def apply(
        self,
        day: ResolvedScheduleDayResponse,
    ) -> ResolvedScheduleDayResponse:
        holiday = await (
            self.holidays
            .resolve_workspace_holiday_for_date(
                holiday_date=(
                    day.schedule_date
                )
            )
        )

        if holiday is None:
            return day

        return day.model_copy(
            update={
                "is_holiday": True,
                "holiday_id": holiday.id,
                "holiday_name": (
                    holiday.name
                ),
                "holiday_treatment": (
                    holiday.treatment
                ),
            }
        )


__all__ = [
    "ShiftHolidayContextService",
]