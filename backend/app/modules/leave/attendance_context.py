from __future__ import annotations

import uuid
from dataclasses import (
    dataclass,
)
from datetime import date

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.modules.leave.consumption import (
    LeaveConsumptionService,
)


@dataclass(
    frozen=True,
    slots=True,
)
class LeaveAttendanceContext:
    employee_id: uuid.UUID
    attendance_date: date

    approved_leave: bool

    leave_request_id: (
        uuid.UUID | None
    )

    paid_leave: bool

    scheduled_minutes: int
    paid_leave_minutes: int
    unpaid_leave_minutes: int

    suppress_absence: bool
    suppress_late: bool


class LeaveAttendanceContextService:
    """
    Attendance-facing Leave context.

    Attendance can use this contract before assigning
    absence or late classifications.

    Approved leave suppresses normal absence/late signals.

    Paid/unpaid treatment remains available separately for
    downstream attendance and payroll logic.
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

        self.consumption = (
            LeaveConsumptionService(
                session
            )
        )

    async def for_employee_date(
        self,
        *,
        employee_id: uuid.UUID,
        attendance_date: date,
    ) -> LeaveAttendanceContext:
        result = await (
            self.consumption
            .for_employee_date(
                employee_id=(
                    employee_id
                ),
                leave_date=(
                    attendance_date
                ),
            )
        )

        return LeaveAttendanceContext(
            employee_id=(
                employee_id
            ),
            attendance_date=(
                attendance_date
            ),
            approved_leave=(
                result
                .covered_by_approved_leave
            ),
            leave_request_id=(
                result.request_id
            ),
            paid_leave=(
                result.is_paid_leave
            ),
            scheduled_minutes=(
                result.scheduled_minutes
            ),
            paid_leave_minutes=(
                result
                .paid_leave_minutes
            ),
            unpaid_leave_minutes=(
                result
                .unpaid_leave_minutes
            ),
            suppress_absence=(
                result.suppress_absence
            ),
            suppress_late=(
                result.suppress_late
            ),
        )


__all__ = [
    "LeaveAttendanceContext",
    "LeaveAttendanceContextService",
]