from __future__ import annotations

import uuid
from dataclasses import (
    dataclass,
)
from datetime import (
    date,
    timedelta,
)

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
class PayrollLeaveDay:
    leave_date: date

    request_id: (
        uuid.UUID | None
    )

    leave_type_id: (
        uuid.UUID | None
    )

    is_paid_leave: bool

    scheduled_minutes: int
    paid_leave_minutes: int
    unpaid_leave_minutes: int


@dataclass(
    frozen=True,
    slots=True,
)
class PayrollLeavePeriod:
    employee_id: uuid.UUID

    period_start: date
    period_end: date

    approved_leave_days: int
    paid_leave_days: int
    unpaid_leave_days: int

    paid_leave_minutes: int
    unpaid_leave_minutes: int

    days: tuple[
        PayrollLeaveDay,
        ...,
    ]


class LeavePayrollContextService:
    """
    Payroll-facing Leave contract.

    Payroll Phase 12.3 can consume this service without needing
    to understand Leave ORM internals.
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.consumption = (
            LeaveConsumptionService(
                session
            )
        )

    async def for_period(
        self,
        *,
        employee_id: uuid.UUID,
        period_start: date,
        period_end: date,
    ) -> PayrollLeavePeriod:
        if period_end < period_start:
            raise ValueError(
                "period_end cannot be "
                "before period_start."
            )

        current = period_start

        items: list[
            PayrollLeaveDay
        ] = []

        while current <= period_end:
            result = await (
                self.consumption
                .for_employee_date(
                    employee_id=employee_id,
                    leave_date=current,
                )
            )

            if (
                result
                .chargeable_leave_day
            ):
                items.append(
                    PayrollLeaveDay(
                        leave_date=current,
                        request_id=(
                            result.request_id
                        ),
                        leave_type_id=(
                            result
                            .leave_type_id
                        ),
                        is_paid_leave=(
                            result
                            .is_paid_leave
                        ),
                        scheduled_minutes=(
                            result
                            .scheduled_minutes
                        ),
                        paid_leave_minutes=(
                            result
                            .paid_leave_minutes
                        ),
                        unpaid_leave_minutes=(
                            result
                            .unpaid_leave_minutes
                        ),
                    )
                )

            current += timedelta(
                days=1
            )

        paid_days = sum(
            1
            for item in items
            if item.is_paid_leave
        )

        unpaid_days = (
            len(items)
            - paid_days
        )

        return PayrollLeavePeriod(
            employee_id=employee_id,
            period_start=period_start,
            period_end=period_end,
            approved_leave_days=(
                len(items)
            ),
            paid_leave_days=(
                paid_days
            ),
            unpaid_leave_days=(
                unpaid_days
            ),
            paid_leave_minutes=sum(
                item.paid_leave_minutes
                for item in items
            ),
            unpaid_leave_minutes=sum(
                item.unpaid_leave_minutes
                for item in items
            ),
            days=tuple(
                items
            ),
        )


__all__ = [
    "PayrollLeaveDay",
    "PayrollLeavePeriod",
    "LeavePayrollContextService",
]