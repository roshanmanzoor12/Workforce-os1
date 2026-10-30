from __future__ import annotations

import uuid
from datetime import date

from app.modules.leave.payroll_context import (
    PayrollLeaveDay,
    PayrollLeavePeriod,
)


def test_paid_leave_period_math_contract():
    employee_id = uuid.uuid4()

    request_id = uuid.uuid4()
    leave_type_id = uuid.uuid4()

    day = PayrollLeaveDay(
        leave_date=date(
            2026,
            10,
            5,
        ),
        request_id=request_id,
        leave_type_id=(
            leave_type_id
        ),
        is_paid_leave=True,
        scheduled_minutes=480,
        paid_leave_minutes=480,
        unpaid_leave_minutes=0,
    )

    period = PayrollLeavePeriod(
        employee_id=employee_id,
        period_start=date(
            2026,
            10,
            1,
        ),
        period_end=date(
            2026,
            10,
            31,
        ),
        approved_leave_days=1,
        paid_leave_days=1,
        unpaid_leave_days=0,
        paid_leave_minutes=480,
        unpaid_leave_minutes=0,
        days=(
            day,
        ),
    )

    assert (
        period.paid_leave_days
        == 1
    )

    assert (
        period.paid_leave_minutes
        == 480
    )


def test_unpaid_leave_period_math_contract():
    day = PayrollLeaveDay(
        leave_date=date(
            2026,
            10,
            7,
        ),
        request_id=uuid.uuid4(),
        leave_type_id=uuid.uuid4(),
        is_paid_leave=False,
        scheduled_minutes=480,
        paid_leave_minutes=0,
        unpaid_leave_minutes=480,
    )

    assert (
        day.unpaid_leave_minutes
        == 480
    )

    assert (
        day.paid_leave_minutes
        == 0
    )