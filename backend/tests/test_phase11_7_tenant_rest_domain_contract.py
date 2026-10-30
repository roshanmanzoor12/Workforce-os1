from __future__ import annotations

from app.modules.attendance.models import (
    AttendanceEvent,
    AttendanceRecord,
)
from app.modules.employees.models import (
    Department,
    Employee,
    Team,
)


def test_rest_domain_tables_are_stable(
) -> None:
    assert (
        Department.__tablename__
        == "departments"
    )

    assert (
        Team.__tablename__
        == "teams"
    )

    assert (
        Employee.__tablename__
        == "employees"
    )

    assert (
        AttendanceRecord.__tablename__
        == "attendance_records"
    )

    assert (
        AttendanceEvent.__tablename__
        == "attendance_events"
    )


def test_attendance_record_is_employee_scoped(
) -> None:
    foreign_keys = {
        fk.target_fullname
        for fk
        in AttendanceRecord
        .__table__
        .columns["employee_id"]
        .foreign_keys
    }

    assert (
        "employees.id"
        in foreign_keys
    )


def test_attendance_event_is_record_scoped(
) -> None:
    foreign_keys = {
        fk.target_fullname
        for fk
        in AttendanceEvent
        .__table__
        .columns[
            "attendance_record_id"
        ]
        .foreign_keys
    }

    assert (
        "attendance_records.id"
        in foreign_keys
    )


def test_tenant_models_do_not_duplicate_workspace_id(
) -> None:
    for model in (
        Department,
        Team,
        Employee,
        AttendanceRecord,
        AttendanceEvent,
    ):
        columns = {
            column.name
            for column
            in model.__table__.columns
        }

        assert (
            "workspace_id"
            not in columns
        )