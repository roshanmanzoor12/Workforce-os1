from __future__ import annotations

import inspect
from pathlib import Path

from app.modules.leave.calendar_service import (
    LeaveCalendarService,
)
from app.modules.leave.service import (
    LeaveService,
)


def test_calendar_service_is_async():
    assert inspect.iscoroutinefunction(
        LeaveCalendarService
        .chargeable_days
    )

    assert inspect.iscoroutinefunction(
        LeaveCalendarService
        .is_chargeable_day
    )


def test_leave_service_create_request_async():
    assert inspect.iscoroutinefunction(
        LeaveService.create_request
    )


def test_leave_service_uses_schedule_aware_calendar():
    source = (
        Path(
            "app/modules/leave/"
            "service.py"
        )
        .read_text(
            encoding="utf-8"
        )
    )

    assert (
        "self.calendar"
        in source
    )

    assert (
        ".chargeable_days("
        in source
    )


def test_calendar_uses_publication_snapshot_service():
    source = (
        Path(
            "app/modules/leave/"
            "calendar_service.py"
        )
        .read_text(
            encoding="utf-8"
        )
    )

    assert (
        "SchedulePublicationSnapshotService"
        in source
    )

    assert (
        ".resolve_day("
        in source
    )


def test_consumption_bridge_exists():
    source = (
        Path(
            "app/modules/leave/"
            "consumption.py"
        )
        .read_text(
            encoding="utf-8"
        )
    )

    assert (
        "LeaveConsumptionService"
        in source
    )

    assert (
        "paid_leave_minutes"
        in source
    )

    assert (
        "unpaid_leave_minutes"
        in source
    )