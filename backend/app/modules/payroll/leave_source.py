from __future__ import annotations

import uuid
from datetime import (
    date,
    timedelta,
)

from sqlalchemy import (
    select,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.modules.leave.models import (
    LeaveRequest,
    LeaveRequestStatus,
    LeaveType,
)
from app.modules.payroll.source_schemas import (
    PayrollLeaveSource,
    PayrollScheduleSource,
)


class PayrollLeaveSourceService:
    """
    Resolve approved paid/unpaid Leave against payable schedule.

    Important:
    Historical approved requests are NOT filtered by the current
    LeaveType.is_active flag. Deactivating a Leave type must not
    make historical approved leave disappear from payroll.
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def resolve(
        self,
        *,
        employee_id: uuid.UUID,
        period_start: date,
        period_end: date,
        schedule: PayrollScheduleSource,
    ) -> PayrollLeaveSource:
        result = await (
            self.session.execute(
                select(
                    LeaveRequest,
                    LeaveType,
                )
                .join(
                    LeaveType,
                    LeaveType.id
                    == LeaveRequest.leave_type_id,
                )
                .where(
                    LeaveRequest.employee_id
                    == employee_id,

                    LeaveRequest.status
                    == (
                        LeaveRequestStatus
                        .APPROVED
                    ),

                    LeaveRequest.start_date
                    <= period_end,

                    LeaveRequest.end_date
                    >= period_start,
                )
            )
        )

        schedule_minutes = {
            day.schedule_date: (
                day.payable_minutes
            )
            for day in schedule.days
        }

        paid_minutes = 0
        unpaid_minutes = 0

        request_ids: list[
            uuid.UUID
        ] = []

        for (
            request,
            leave_type,
        ) in result.all():
            request_ids.append(
                request.id
            )

            current = max(
                request.start_date,
                period_start,
            )

            last = min(
                request.end_date,
                period_end,
            )

            while current <= last:
                minutes = max(
                    0,
                    int(
                        schedule_minutes.get(
                            current,
                            0,
                        )
                    ),
                )

                if leave_type.is_paid:
                    paid_minutes += minutes

                else:
                    unpaid_minutes += minutes

                current += timedelta(
                    days=1
                )

        return PayrollLeaveSource(
            employee_id=employee_id,
            paid_leave_minutes=(
                paid_minutes
            ),
            unpaid_leave_minutes=(
                unpaid_minutes
            ),
            leave_request_ids=(
                request_ids
            ),
        )


__all__ = [
    "PayrollLeaveSourceService",
]