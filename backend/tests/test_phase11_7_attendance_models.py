from __future__ import annotations

from app.db.tenant_base import (
    TenantBase,
)
from app.modules.attendance.models import (
    AttendanceEvent,
    AttendanceRecord,
)


def test_attendance_record_is_tenant_model(
) -> None:
    assert issubclass(
        AttendanceRecord,
        TenantBase,
    )


def test_attendance_event_is_tenant_model(
) -> None:
    assert issubclass(
        AttendanceEvent,
        TenantBase,
    )


def test_attendance_record_table(
) -> None:
    assert (
        AttendanceRecord.__tablename__
        == "attendance_records"
    )


def test_attendance_event_table(
) -> None:
    assert (
        AttendanceEvent.__tablename__
        == "attendance_events"
    )


def test_attendance_record_columns(
) -> None:
    columns = {
        column.name
        for column
        in AttendanceRecord.__table__.columns
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


def test_attendance_event_columns(
) -> None:
    columns = {
        column.name
        for column
        in AttendanceEvent.__table__.columns
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


def test_attendance_employee_fk(
) -> None:
    column = (
        AttendanceRecord.__table__
        .columns["employee_id"]
    )

    targets = {
        foreign_key.target_fullname
        for foreign_key
        in column.foreign_keys
    }

    assert "employees.id" in targets