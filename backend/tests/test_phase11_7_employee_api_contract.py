from __future__ import annotations

from pathlib import Path


def test_employee_api_uses_authorized_context(
) -> None:
    text = Path(
        "app/modules/employees/api.py"
    ).read_text(
        encoding="utf-8"
    )

    assert "AuthorizedTenantContext" in text
    assert "EmployeeAccessService" in text


def test_employee_api_exposes_department_operations(
) -> None:
    text = Path(
        "app/modules/employees/api.py"
    ).read_text(
        encoding="utf-8"
    )

    required = [
        "create_department",
        "list_departments",
        "get_department",
        "update_department",
        "delete_department",
    ]

    for token in required:
        assert token in text


def test_employee_api_exposes_team_operations(
) -> None:
    text = Path(
        "app/modules/employees/api.py"
    ).read_text(
        encoding="utf-8"
    )

    required = [
        "create_team",
        "list_teams",
        "get_team",
        "update_team",
        "delete_team",
    ]

    for token in required:
        assert token in text


def test_employee_api_exposes_employee_operations(
) -> None:
    text = Path(
        "app/modules/employees/api.py"
    ).read_text(
        encoding="utf-8"
    )

    required = [
        "create_employee",
        "list_employees",
        "get_employee",
        "update_employee",
        "delete_employee",
    ]

    for token in required:
        assert token in text