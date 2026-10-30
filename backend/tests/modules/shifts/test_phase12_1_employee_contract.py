from __future__ import annotations

from app.modules.employees.models import (
    Employee,
    Team,
)
from app.modules.employees.repository import (
    EmployeeRepository,
)


def test_employee_has_schedule_scope_fields():
    columns = {
        column.name
        for column
        in Employee.__table__.columns
    }

    required = {
        "id",
        "user_id",
        "team_id",
        "manager_id",
        "is_active",
    }

    assert required.issubset(
        columns
    )


def test_team_model_is_canonical_employee_team():
    assert (
        Team.__tablename__
        == "teams"
    )


def test_employee_user_link_is_not_fk():
    column = (
        Employee
        .__table__
        .columns[
            "user_id"
        ]
    )

    assert (
        len(
            column.foreign_keys
        )
        == 0
    )


def test_employee_team_is_fk():
    column = (
        Employee
        .__table__
        .columns[
            "team_id"
        ]
    )

    assert (
        len(
            column.foreign_keys
        )
        == 1
    )


def test_employee_manager_is_fk():
    column = (
        Employee
        .__table__
        .columns[
            "manager_id"
        ]
    )

    assert (
        len(
            column.foreign_keys
        )
        == 1
    )


def test_repository_supports_user_lookup():
    assert hasattr(
        EmployeeRepository,
        "get_employee_by_user_id",
    )


def test_repository_supports_employee_lookup():
    assert hasattr(
        EmployeeRepository,
        "get_employee_by_id",
    )


def test_repository_supports_team_lookup():
    assert hasattr(
        EmployeeRepository,
        "get_team_by_id",
    )