from datetime import (
    date,
    time,
)

import pytest
from pydantic import ValidationError

from app.modules.shifts.models import (
    ScheduleExceptionType,
    ShiftAssignmentTargetType,
)
from app.modules.shifts.schemas import (
    ScheduleExceptionCreateRequest,
    SchedulePublishRequest,
    ShiftAssignmentCreateRequest,
    ShiftCreateRequest,
)


def test_regular_shift_schema():
    request = ShiftCreateRequest(
        name="Day Shift",
        timezone="Asia/Karachi",
        start_time=time(9, 0),
        end_time=time(18, 0),
        break_minutes=60,
        working_days=[
            {
                "weekday": 0,
                "is_working_day": True,
            },
            {
                "weekday": 1,
                "is_working_day": True,
            },
        ],
    )

    assert request.name == "Day Shift"
    assert request.break_minutes == 60


def test_non_overnight_shift_rejects_reverse_time():
    with pytest.raises(
        ValidationError
    ):
        ShiftCreateRequest(
            name="Invalid Shift",
            timezone="Asia/Karachi",
            start_time=time(18, 0),
            end_time=time(9, 0),
            is_overnight=False,
        )


def test_overnight_shift_accepts_reverse_time():
    request = ShiftCreateRequest(
        name="Night Shift",
        timezone="Asia/Karachi",
        start_time=time(22, 0),
        end_time=time(6, 0),
        is_overnight=True,
    )

    assert request.is_overnight is True


def test_duplicate_working_days_are_rejected():
    with pytest.raises(
        ValidationError
    ):
        ShiftCreateRequest(
            name="Duplicate Days",
            timezone="Asia/Karachi",
            start_time=time(9, 0),
            end_time=time(17, 0),
            working_days=[
                {
                    "weekday": 0,
                    "is_working_day": True,
                },
                {
                    "weekday": 0,
                    "is_working_day": True,
                },
            ],
        )


def test_assignment_rejects_reverse_effective_range():
    with pytest.raises(
        ValidationError
    ):
        ShiftAssignmentCreateRequest(
            shift_id=(
                "11111111-1111-1111-"
                "1111-111111111111"
            ),
            target_type=(
                ShiftAssignmentTargetType
                .EMPLOYEE
            ),
            target_id=(
                "22222222-2222-2222-"
                "2222-222222222222"
            ),
            effective_from=date(
                2026,
                10,
                10,
            ),
            effective_to=date(
                2026,
                10,
                1,
            ),
        )


def test_custom_shift_requires_times():
    with pytest.raises(
        ValidationError
    ):
        ScheduleExceptionCreateRequest(
            employee_id=(
                "33333333-3333-3333-"
                "3333-333333333333"
            ),
            exception_date=date(
                2026,
                10,
                5,
            ),
            exception_type=(
                ScheduleExceptionType
                .CUSTOM_SHIFT
            ),
        )


def test_schedule_publication_rejects_reverse_range():
    with pytest.raises(
        ValidationError
    ):
        SchedulePublishRequest(
            period_start=date(
                2026,
                10,
                31,
            ),
            period_end=date(
                2026,
                10,
                1,
            ),
        )