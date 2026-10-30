from __future__ import annotations

import inspect
import uuid
from datetime import date

from app.modules.attendance.leave_bridge import (
    AttendanceLeaveDecision,
    AttendanceLeaveBridge,
)


def test_attendance_leave_decision_contract():
    fields = set(
        AttendanceLeaveDecision
        .__dataclass_fields__
    )

    assert fields == {
        "employee_id",
        "attendance_date",
        "approved_leave",
        "paid_leave",
        "leave_request_id",
        "scheduled_minutes",
        "paid_leave_minutes",
        "unpaid_leave_minutes",
        "allow_absent_classification",
        "allow_late_classification",
    }


def test_bridge_method_is_async():
    assert inspect.iscoroutinefunction(
        AttendanceLeaveBridge
        .decision_for_day
    )


def test_approved_leave_decision_can_block_absence():
    decision = AttendanceLeaveDecision(
        employee_id=uuid.uuid4(),
        attendance_date=date(
            2026,
            10,
            10,
        ),
        approved_leave=True,
        paid_leave=True,
        leave_request_id=(
            uuid.uuid4()
        ),
        scheduled_minutes=480,
        paid_leave_minutes=480,
        unpaid_leave_minutes=0,
        allow_absent_classification=False,
        allow_late_classification=False,
    )

    assert (
        decision
        .allow_absent_classification
        is False
    )

    assert (
        decision
        .allow_late_classification
        is False
    )