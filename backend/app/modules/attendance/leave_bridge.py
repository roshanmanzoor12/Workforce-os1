from __future__ import annotations

import uuid
from dataclasses import (
    dataclass,
)
from datetime import date

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.modules.leave.attendance_context import (
    LeaveAttendanceContextService,
)


@dataclass(
    frozen=True,
    slots=True,
)
class AttendanceLeaveDecision:
    employee_id: uuid.UUID
    attendance_date: date

    approved_leave: bool
    paid_leave: bool

    leave_request_id: (
        uuid.UUID | None
    )

    scheduled_minutes: int

    paid_leave_minutes: int
    unpaid_leave_minutes: int

    allow_absent_classification: bool
    allow_late_classification: bool


class AttendanceLeaveBridge:
    """
    Attendance-domain adapter over Leave.

    Attendance code should call this before assigning an automatic
    absent/late state.

    This adapter deliberately does not mutate AttendanceDay records.
    It returns a deterministic classification decision that the
    existing Attendance engine can consume.
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.leave = (
            LeaveAttendanceContextService(
                session
            )
        )

    async def decision_for_day(
        self,
        *,
        employee_id: uuid.UUID,
        attendance_date: date,
    ) -> AttendanceLeaveDecision:
        context = await (
            self.leave
            .for_employee_date(
                employee_id=employee_id,
                attendance_date=(
                    attendance_date
                ),
            )
        )

        return AttendanceLeaveDecision(
            employee_id=employee_id,
            attendance_date=(
                attendance_date
            ),
            approved_leave=(
                context.approved_leave
            ),
            paid_leave=(
                context.paid_leave
            ),
            leave_request_id=(
                context
                .leave_request_id
            ),
            scheduled_minutes=(
                context
                .scheduled_minutes
            ),
            paid_leave_minutes=(
                context
                .paid_leave_minutes
            ),
            unpaid_leave_minutes=(
                context
                .unpaid_leave_minutes
            ),
            allow_absent_classification=(
                not context
                .suppress_absence
            ),
            allow_late_classification=(
                not context
                .suppress_late
            ),
        )


__all__ = [
    "AttendanceLeaveDecision",
    "AttendanceLeaveBridge",
]