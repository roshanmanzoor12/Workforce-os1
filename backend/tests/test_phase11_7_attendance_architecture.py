from __future__ import annotations

from pathlib import Path

from app.modules.attendance.models import (
    AttendanceDay,
    AttendanceEvent,
    AttendanceRecord,
)


def test_attendance_links_employee(
) -> None:
    column = (
        AttendanceRecord.__table__
        .columns["employee_id"]
    )

    targets = {
        str(
            foreign_key.target_fullname
        )
        for foreign_key
        in column.foreign_keys
    }

    assert (
        "employees.id"
        in targets
    )


def test_event_links_attendance_record(
) -> None:
    column = (
        AttendanceEvent.__table__
        .columns[
            "attendance_record_id"
        ]
    )

    targets = {
        str(
            foreign_key.target_fullname
        )
        for foreign_key
        in column.foreign_keys
    }

    assert (
        "attendance_records.id"
        in targets
    )


def test_attendance_day_is_compatibility_alias(
) -> None:
    assert (
        AttendanceDay
        is AttendanceRecord
    )

    assert (
        AttendanceDay.__tablename__
        == "attendance_records"
    )


def test_attendance_has_no_workspace_id(
) -> None:
    columns = {
        column.name
        for column
        in AttendanceRecord
        .__table__
        .columns
    }

    assert (
        "workspace_id"
        not in columns
    )


def test_attendance_has_source_attribution(
) -> None:
    assert (
        "source"
        in AttendanceRecord
        .__table__
        .columns
    )

    assert (
        "source"
        in AttendanceEvent
        .__table__
        .columns
    )


def test_attendance_has_audit_actor_fields(
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

    assert {
        "created_by_user_id",
        "updated_by_user_id",
    }.issubset(
        record_columns
    )

    assert (
        "actor_user_id"
        in event_columns
    )


def test_attendance_uses_minutes_contract(
) -> None:
    columns = {
        column.name
        for column
        in AttendanceRecord
        .__table__
        .columns
    }

    assert {
        "worked_minutes",
        "break_minutes",
    }.issubset(
        columns
    )

    assert (
        "worked_seconds"
        not in columns
    )

    assert (
        "break_seconds"
        not in columns
    )


def test_attendance_uses_record_contract(
) -> None:
    record_columns = {
        column.name
        for column
        in AttendanceRecord
        .__table__
        .columns
    }

    assert {
        "attendance_date",
        "check_in_at",
        "check_out_at",
        "notes",
    }.issubset(
        record_columns
    )

    assert (
        "work_date"
        not in record_columns
    )

    assert (
        "first_check_in_at"
        not in record_columns
    )

    assert (
        "last_check_out_at"
        not in record_columns
    )


def test_event_uses_record_foreign_key(
) -> None:
    columns = {
        column.name
        for column
        in AttendanceEvent
        .__table__
        .columns
    }

    assert (
        "attendance_record_id"
        in columns
    )

    assert (
        "attendance_day_id"
        not in columns
    )


def test_attendance_module_has_no_invasive_capture(
) -> None:
    root = Path(
        "app/modules/attendance"
    )

    forbidden = [
        "keylogger",
        "keylogging",
        "clipboard_capture",
        "typed_text",
        "password_capture",
        "mouse_coordinates",
        "stealth_mode",
    ]

    for path in root.rglob(
        "*.py"
    ):
        content = path.read_text(
            encoding="utf-8",
            errors="ignore",
        ).lower()

        for token in forbidden:
            assert (
                token
                not in content
            )


def test_service_uses_existing_employee_repository(
) -> None:
    content = Path(
        "app/modules/attendance/"
        "service.py"
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "EmployeeRepository"
        in content
    )

    assert (
        "EMPLOYMENT_STATUS_TERMINATED"
        in content
    )