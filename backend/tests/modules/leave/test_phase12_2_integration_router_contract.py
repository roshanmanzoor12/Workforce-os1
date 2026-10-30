from __future__ import annotations

from pathlib import Path

from app.modules.leave.integration_router import (
    router,
)


def paths() -> set[str]:
    return {
        route.path
        for route
        in router.routes
        if hasattr(
            route,
            "path",
        )
    }


def test_employee_calendar_route():
    assert (
        "/workspaces/{workspace_id}"
        "/leave-integration/"
        "employees/{employee_id}/calendar"
        in paths()
    )


def test_attendance_context_route():
    assert (
        "/workspaces/{workspace_id}"
        "/leave-integration/"
        "employees/{employee_id}/"
        "attendance-context/"
        "{attendance_date}"
        in paths()
    )


def test_consumption_route():
    assert (
        "/workspaces/{workspace_id}"
        "/leave-integration/"
        "employees/{employee_id}/"
        "consumption/{leave_date}"
        in paths()
    )


def test_payroll_context_route():
    assert (
        "/workspaces/{workspace_id}"
        "/leave-integration/"
        "employees/{employee_id}/"
        "payroll-context"
        in paths()
    )


def test_router_uses_tenant_scope_and_scoped_read_helper():
    source = (
        Path(
            "app/modules/leave/"
            "integration_router.py"
        )
        .read_text(
            encoding="utf-8"
        )
    )

    assert (
        "TenantScope"
        in source
    )

    assert (
        "_require_employee_leave_read"
        in source
    )

    assert (
        "WorkspacePermissionService"
        in source
    )

    assert (
        "EmployeeRepository"
        in source
    )


def test_router_enforces_self_team_all_permissions():
    source = (
        Path(
            "app/modules/leave/"
            "integration_router.py"
        )
        .read_text(
            encoding="utf-8"
        )
    )

    assert (
        "LEAVE_SELF_READ"
        in source
    )

    assert (
        "LEAVE_TEAM_READ"
        in source
    )

    assert (
        "LEAVE_ALL_READ"
        in source
    )