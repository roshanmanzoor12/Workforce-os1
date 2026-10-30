from __future__ import annotations

import inspect

from app.modules.leave.attendance_context import (
    LeaveAttendanceContext,
    LeaveAttendanceContextService,
)
from app.modules.leave.payroll_context import (
    LeavePayrollContextService,
    PayrollLeaveDay,
    PayrollLeavePeriod,
)


def test_attendance_context_fields():
    fields = set(
        LeaveAttendanceContext
        .__dataclass_fields__
    )

    expected = {
        "employee_id",
        "attendance_date",
        "approved_leave",
        "leave_request_id",
        "paid_leave",
        "scheduled_minutes",
        "paid_leave_minutes",
        "unpaid_leave_minutes",
        "suppress_absence",
        "suppress_late",
    }

    assert fields == expected


def test_attendance_service_async_contract():
    assert inspect.iscoroutinefunction(
        LeaveAttendanceContextService
        .for_employee_date
    )


def test_payroll_day_fields():
    fields = set(
        PayrollLeaveDay
        .__dataclass_fields__
    )

    assert fields == {
        "leave_date",
        "request_id",
        "leave_type_id",
        "is_paid_leave",
        "scheduled_minutes",
        "paid_leave_minutes",
        "unpaid_leave_minutes",
    }


def test_payroll_period_fields():
    fields = set(
        PayrollLeavePeriod
        .__dataclass_fields__
    )

    assert fields == {
        "employee_id",
        "period_start",
        "period_end",
        "approved_leave_days",
        "paid_leave_days",
        "unpaid_leave_days",
        "paid_leave_minutes",
        "unpaid_leave_minutes",
        "days",
    }


def test_payroll_service_async_contract():
    assert inspect.iscoroutinefunction(
        LeavePayrollContextService
        .for_period
    )