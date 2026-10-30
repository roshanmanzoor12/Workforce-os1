from __future__ import annotations

import inspect

from app.modules.leave.calendar_query import (
    LeaveCalendarQueryService,
)
from app.modules.leave.calendar_schemas import (
    LeaveCalendarEntryResponse,
    LeaveCalendarResponse,
)


def test_calendar_query_is_async():
    assert inspect.iscoroutinefunction(
        LeaveCalendarQueryService
        .employee_calendar
    )


def test_calendar_response_contract():
    fields = set(
        LeaveCalendarResponse
        .model_fields
    )

    assert fields == {
        "employee_id",
        "start_date",
        "end_date",
        "items",
        "total_entries",
    }


def test_calendar_entry_contract():
    fields = set(
        LeaveCalendarEntryResponse
        .model_fields
    )

    expected = {
        "request_id",
        "employee_id",
        "leave_type_id",
        "leave_type_name",
        "leave_type_code",
        "calendar_date",
        "request_start_date",
        "request_end_date",
        "request_status",
        "is_paid_leave",
        "chargeable_leave_day",
        "scheduled_minutes",
        "paid_leave_minutes",
        "unpaid_leave_minutes",
    }

    assert fields == expected