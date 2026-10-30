from __future__ import annotations

import uuid
from datetime import date

from pydantic import (
    BaseModel,
    ConfigDict,
)


class LeaveIntegrationSchema(
    BaseModel
):
    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )


class LeaveAttendanceContextResponse(
    LeaveIntegrationSchema
):
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


class PayrollLeaveDayResponse(
    LeaveIntegrationSchema
):
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


class PayrollLeavePeriodResponse(
    LeaveIntegrationSchema
):
    employee_id: uuid.UUID

    period_start: date
    period_end: date

    approved_leave_days: int

    paid_leave_days: int
    unpaid_leave_days: int

    paid_leave_minutes: int
    unpaid_leave_minutes: int

    days: tuple[
        PayrollLeaveDayResponse,
        ...,
    ]


__all__ = [
    "LeaveAttendanceContextResponse",
    "PayrollLeaveDayResponse",
    "PayrollLeavePeriodResponse",
]