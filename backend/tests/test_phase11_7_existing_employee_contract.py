from __future__ import annotations

from app.db.tenant_base import (
    TenantBase,
)
from app.modules.employees.models import (
    Department,
    Employee,
    Team,
)


def test_department_is_tenant_model(
) -> None:
    assert issubclass(
        Department,
        TenantBase,
    )


def test_team_is_tenant_model(
) -> None:
    assert issubclass(
        Team,
        TenantBase,
    )


def test_employee_is_tenant_model(
) -> None:
    assert issubclass(
        Employee,
        TenantBase,
    )


def test_employee_has_global_user_link(
) -> None:
    assert (
        "user_id"
        in Employee.__table__.columns
    )


def test_employee_user_link_has_no_cross_db_fk(
) -> None:
    column = (
        Employee.__table__.columns[
            "user_id"
        ]
    )

    assert len(
        column.foreign_keys
    ) == 0


def test_employee_has_org_links(
) -> None:
    columns = {
        column.name
        for column
        in Employee.__table__.columns
    }

    assert {
        "department_id",
        "team_id",
        "manager_id",
    }.issubset(
        columns
    )


def test_employee_has_lifecycle_fields(
) -> None:
    columns = {
        column.name
        for column
        in Employee.__table__.columns
    }

    assert {
        "employment_status",
        "hire_date",
        "termination_date",
        "is_active",
    }.issubset(
        columns
    )