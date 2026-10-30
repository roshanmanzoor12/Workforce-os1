from __future__ import annotations

import uuid
from datetime import date
from types import SimpleNamespace

from app.modules.leave.consumption import (
    LeaveConsumptionService,
)


EMPLOYEE_ID = uuid.uuid4()

REQUEST_ID = uuid.uuid4()

LEAVE_TYPE_ID = uuid.uuid4()

LEAVE_DATE = date(
    2026,
    10,
    5,
)


def request():
    return SimpleNamespace(
        id=REQUEST_ID,
        employee_id=EMPLOYEE_ID,
        leave_type_id=(
            LEAVE_TYPE_ID
        ),
    )


def leave_type(
    *,
    paid: bool,
):
    return SimpleNamespace(
        id=LEAVE_TYPE_ID,
        is_paid=paid,
    )


def schedule(
    *,
    working: bool = True,
    holiday: bool = False,
    payable_minutes: int = 480,
):
    return SimpleNamespace(
        is_working_day=working,
        is_holiday=holiday,
        payable_minutes=(
            payable_minutes
        ),
    )


def test_paid_leave_consumption():
    result = (
        LeaveConsumptionService
        .classify(
            employee_id=EMPLOYEE_ID,
            leave_date=LEAVE_DATE,
            leave_request=request(),
            leave_type=leave_type(
                paid=True
            ),
            schedule_day=schedule(),
        )
    )

    assert (
        result
        .covered_by_approved_leave
        is True
    )

    assert (
        result
        .chargeable_leave_day
        is True
    )

    assert (
        result
        .paid_leave_minutes
        == 480
    )

    assert (
        result
        .unpaid_leave_minutes
        == 0
    )

    assert (
        result.suppress_absence
        is True
    )


def test_unpaid_leave_consumption():
    result = (
        LeaveConsumptionService
        .classify(
            employee_id=EMPLOYEE_ID,
            leave_date=LEAVE_DATE,
            leave_request=request(),
            leave_type=leave_type(
                paid=False
            ),
            schedule_day=schedule(),
        )
    )

    assert (
        result
        .paid_leave_minutes
        == 0
    )

    assert (
        result
        .unpaid_leave_minutes
        == 480
    )


def test_no_approved_leave():
    result = (
        LeaveConsumptionService
        .classify(
            employee_id=EMPLOYEE_ID,
            leave_date=LEAVE_DATE,
            leave_request=None,
            leave_type=None,
            schedule_day=schedule(),
        )
    )

    assert (
        result
        .covered_by_approved_leave
        is False
    )

    assert (
        result
        .chargeable_leave_day
        is False
    )

    assert (
        result.suppress_absence
        is False
    )


def test_holiday_does_not_create_leave_minutes():
    result = (
        LeaveConsumptionService
        .classify(
            employee_id=EMPLOYEE_ID,
            leave_date=LEAVE_DATE,
            leave_request=request(),
            leave_type=leave_type(
                paid=True
            ),
            schedule_day=schedule(
                holiday=True
            ),
        )
    )

    assert (
        result
        .chargeable_leave_day
        is False
    )

    assert (
        result
        .paid_leave_minutes
        == 0
    )

    assert (
        result
        .unpaid_leave_minutes
        == 0
    )


def test_non_working_day_has_no_leave_minutes():
    result = (
        LeaveConsumptionService
        .classify(
            employee_id=EMPLOYEE_ID,
            leave_date=LEAVE_DATE,
            leave_request=request(),
            leave_type=leave_type(
                paid=False
            ),
            schedule_day=schedule(
                working=False
            ),
        )
    )

    assert (
        result
        .chargeable_leave_day
        is False
    )

    assert (
        result
        .unpaid_leave_minutes
        == 0
    )