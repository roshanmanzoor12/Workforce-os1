from __future__ import annotations

from app.modules.attendance.models import (
    AttendanceEvent,
    AttendanceRecord,
)


def test_attendance_record_contract(
) -> None:
    columns = {
        column.name
        for column
        in AttendanceRecord
        .__table__
        .columns
    }

    required = {
        "id",
        "employee_id",
        "attendance_date",
        "status",
        "source",
        "check_in_at",
        "check_out_at",
        "worked_minutes",
        "break_minutes",
        "notes",
        "created_by_user_id",
        "updated_by_user_id",
        "created_at",
        "updated_at",
    }

    assert required.issubset(
        columns
    )


def test_attendance_event_contract(
) -> None:
    columns = {
        column.name
        for column
        in AttendanceEvent
        .__table__
        .columns
    }

    required = {
        "id",
        "attendance_record_id",
        "employee_id",
        "event_type",
        "source",
        "occurred_at",
        "actor_user_id",
        "notes",
        "created_at",
        "updated_at",
    }

    assert required.issubset(
        columns
    )


def test_old_attendance_columns_are_gone(
) -> None:
    record_columns = {
        column.name
        for column
        in AttendanceRecord
        .__table__
        .columns
    }

    event_columns = {
        column.name
        for column
        in AttendanceEvent
        .__table__
        .columns
    }

    forbidden_record = {
        "work_date",
        "first_check_in_at",
        "last_check_out_at",
        "worked_seconds",
        "break_seconds",
    }

    forbidden_event = {
        "attendance_day_id",
    }

    assert not (
        forbidden_record
        & record_columns
    )

    assert not (
        forbidden_event
        & event_columns
    )