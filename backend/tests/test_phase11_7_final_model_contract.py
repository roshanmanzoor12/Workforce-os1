from __future__ import annotations

from app.db.tenant_base import (
    TenantBase,
)
from app.modules.attendance.models import (
    AttendanceDay,
    AttendanceEvent,
    AttendanceRecord,
)
from app.modules.employees.models import (
    Department,
    Employee,
    Team,
)


def test_all_phase11_7_models_are_tenant_scoped(
) -> None:
    models = [
        Department,
        Team,
        Employee,
        AttendanceRecord,
        AttendanceEvent,
    ]

    for model in models:
        assert issubclass(
            model,
            TenantBase,
        )


def test_phase11_7_table_names(
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


def test_attendance_day_is_alias_only(
) -> None:
    assert (
        AttendanceDay
        is AttendanceRecord
    )


def test_employee_global_user_link_has_no_cross_db_fk(
) -> None:
    column = (
        Employee.__table__
        .columns["user_id"]
    )

    assert (
        len(column.foreign_keys)
        == 0
    )


def test_attendance_employee_fk(
) -> None:
    targets = {
        fk.target_fullname
        for fk
        in AttendanceRecord
        .__table__
        .columns["employee_id"]
        .foreign_keys
    }

    assert (
        "employees.id"
        in targets
    )


def test_event_record_fk(
) -> None:
    targets = {
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
        in targets
    )


def test_tenant_models_do_not_duplicate_workspace_id(
) -> None:
    models = [
        Department,
        Team,
        Employee,
        AttendanceRecord,
        AttendanceEvent,
    ]

    for model in models:
        columns = {
            column.name
            for column
            in model.__table__.columns
        }

        assert (
            "workspace_id"
            not in columns
        )