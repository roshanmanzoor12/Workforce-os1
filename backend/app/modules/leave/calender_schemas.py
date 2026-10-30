from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from app.modules.leave.models import (
    LeaveRequestStatus,
)


class LeaveCalendarSchema(
    BaseModel
):
    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )


class LeaveCalendarEntryResponse(
    LeaveCalendarSchema
):
    request_id: uuid.UUID

    employee_id: uuid.UUID
    leave_type_id: uuid.UUID

    leave_type_name: str
    leave_type_code: str

    calendar_date: date

    request_start_date: date
    request_end_date: date

    request_status: (
        LeaveRequestStatus
    )

    is_paid_leave: bool
    chargeable_leave_day: bool

    scheduled_minutes: int
    paid_leave_minutes: int
    unpaid_leave_minutes: int


class LeaveCalendarResponse(
    LeaveCalendarSchema
):
    employee_id: uuid.UUID

    start_date: date
    end_date: date

    items: list[
        LeaveCalendarEntryResponse
    ] = Field(
        default_factory=list
    )

    total_entries: int


class LeaveConsumptionDayResponse(
    LeaveCalendarSchema
):
    employee_id: uuid.UUID
    leave_date: date

    request_id: (
        uuid.UUID | None
    )

    leave_type_id: (
        uuid.UUID | None
    )

    covered_by_approved_leave: bool
    chargeable_leave_day: bool
    is_paid_leave: bool

    scheduled_minutes: int
    paid_leave_minutes: int
    unpaid_leave_minutes: int

    suppress_absence: bool
    suppress_late: bool


class LeaveBalanceSummaryResponse(
    LeaveCalendarSchema
):
    employee_id: uuid.UUID
    balance_year: int

    allocated_days: Decimal
    carried_forward_days: Decimal
    adjustment_days: Decimal

    used_days: Decimal
    pending_days: Decimal

    available_days: Decimal


__all__ = [
    "LeaveCalendarEntryResponse",
    "LeaveCalendarResponse",
    "LeaveConsumptionDayResponse",
    "LeaveBalanceSummaryResponse",
]