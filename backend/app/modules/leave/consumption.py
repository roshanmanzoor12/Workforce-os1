from __future__ import annotations

import uuid
from dataclasses import (
    dataclass,
)
from datetime import date
from typing import Any

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
from app.modules.shifts.publication_snapshot import (
    SchedulePublicationSnapshotService,
)


@dataclass(
    frozen=True,
    slots=True,
)
class LeaveDayConsumption:
    employee_id: uuid.UUID
    leave_date: date

    request_id: uuid.UUID | None
    leave_type_id: uuid.UUID | None

    covered_by_approved_leave: bool
    chargeable_leave_day: bool
    is_paid_leave: bool

    scheduled_minutes: int
    paid_leave_minutes: int
    unpaid_leave_minutes: int

    suppress_absence: bool
    suppress_late: bool


class LeaveConsumptionService:
    """
    Canonical bridge between Leave and downstream domains.

    Consumers:
        - Attendance
        - Payroll

    Only APPROVED leave is authoritative for downstream
    attendance/payroll classification.
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
    # APPROVED LEAVE LOOKUP
    # =====================================================

    async def approved_leave_for_date(
        self,
        *,
        employee_id: uuid.UUID,
        leave_date: date,
    ) -> tuple[
        LeaveRequest,
        LeaveType,
    ] | None:
        statement = (
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
                <= leave_date,
                LeaveRequest.end_date
                >= leave_date,
                LeaveType.is_active.is_(
                    True
                ),
            )
            .order_by(
                LeaveRequest
                .created_at
                .desc()
            )
            .limit(1)
        )

        result = await (
            self.session.execute(
                statement
            )
        )

        row = result.first()

        if row is None:
            return None

        return (
            row[0],
            row[1],
        )

    # =====================================================
    # PURE CLASSIFICATION
    # =====================================================

    @staticmethod
    def classify(
        *,
        employee_id: uuid.UUID,
        leave_date: date,
        leave_request: (
            LeaveRequest | None
        ),
        leave_type: (
            LeaveType | None
        ),
        schedule_day: Any,
    ) -> LeaveDayConsumption:
        scheduled_minutes = int(
            getattr(
                schedule_day,
                "payable_minutes",
                0,
            )
            or 0
        )

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

        covered_by_approved_leave = (
            leave_request is not None
            and leave_type is not None
        )

        chargeable_leave_day = (
            covered_by_approved_leave
            and is_working_day
            and not is_holiday
        )

        is_paid_leave = bool(
            chargeable_leave_day
            and leave_type is not None
            and leave_type.is_paid
        )

        paid_leave_minutes = (
            scheduled_minutes
            if is_paid_leave
            else 0
        )

        unpaid_leave_minutes = (
            scheduled_minutes
            if (
                chargeable_leave_day
                and not is_paid_leave
            )
            else 0
        )

        return LeaveDayConsumption(
            employee_id=(
                employee_id
            ),
            leave_date=(
                leave_date
            ),
            request_id=(
                leave_request.id
                if leave_request
                else None
            ),
            leave_type_id=(
                leave_type.id
                if leave_type
                else None
            ),
            covered_by_approved_leave=(
                covered_by_approved_leave
            ),
            chargeable_leave_day=(
                chargeable_leave_day
            ),
            is_paid_leave=(
                is_paid_leave
            ),
            scheduled_minutes=(
                scheduled_minutes
            ),
            paid_leave_minutes=(
                paid_leave_minutes
            ),
            unpaid_leave_minutes=(
                unpaid_leave_minutes
            ),
            suppress_absence=(
                covered_by_approved_leave
            ),
            suppress_late=(
                covered_by_approved_leave
            ),
        )

    # =====================================================
    # AUTHORITATIVE DAY CONTEXT
    # =====================================================

    async def for_employee_date(
        self,
        *,
        employee_id: uuid.UUID,
        leave_date: date,
    ) -> LeaveDayConsumption:
        approved_leave = await (
            self.approved_leave_for_date(
                employee_id=(
                    employee_id
                ),
                leave_date=(
                    leave_date
                ),
            )
        )

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

        if approved_leave is None:
            leave_request = None
            leave_type = None

        else:
            (
                leave_request,
                leave_type,
            ) = approved_leave

        return self.classify(
            employee_id=(
                employee_id
            ),
            leave_date=(
                leave_date
            ),
            leave_request=(
                leave_request
            ),
            leave_type=(
                leave_type
            ),
            schedule_day=(
                schedule_day
            ),
        )


__all__ = [
    "LeaveDayConsumption",
    "LeaveConsumptionService",
]