from __future__ import annotations

from app.modules.leave.router import (
    router,
)


def route_paths() -> set[str]:
    return {
        route.path
        for route
        in router.routes
    }


def test_leave_type_routes():
    paths = route_paths()

    assert (
        "/workspaces/{workspace_id}"
        "/leave/types"
        in paths
    )

    assert (
        "/workspaces/{workspace_id}"
        "/leave/types/{leave_type_id}"
        in paths
    )


def test_leave_policy_routes():
    paths = route_paths()

    assert (
        "/workspaces/{workspace_id}"
        "/leave/policies"
        in paths
    )

    assert (
        "/workspaces/{workspace_id}"
        "/leave/policies/{leave_type_id}"
        in paths
    )


def test_self_leave_routes():
    paths = route_paths()

    assert (
        "/workspaces/{workspace_id}"
        "/leave/me/requests"
        in paths
    )

    assert (
        "/workspaces/{workspace_id}"
        "/leave/me/requests/"
        "{request_id}/cancel"
        in paths
    )

    assert (
        "/workspaces/{workspace_id}"
        "/leave/me/balances"
        in paths
    )


def test_approval_routes():
    paths = route_paths()

    assert (
        "/workspaces/{workspace_id}"
        "/leave/requests/"
        "{request_id}/approve"
        in paths
    )

    assert (
        "/workspaces/{workspace_id}"
        "/leave/requests/"
        "{request_id}/reject"
        in paths
    )


def test_balance_management_route():
    paths = route_paths()

    assert (
        "/workspaces/{workspace_id}"
        "/leave/employees/"
        "{employee_id}/balances/"
        "{leave_type_id}/"
        "{balance_year}/adjustments"
        in paths
    )