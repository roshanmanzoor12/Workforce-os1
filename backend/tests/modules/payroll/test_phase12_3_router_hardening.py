from __future__ import annotations

import inspect

from app.modules.payroll.router import (
    router,
)


def paths() -> set[str]:
    return {
        route.path
        for route in router.routes
        if hasattr(
            route,
            "path",
        )
    }


def test_run_detail_route_exists():
    assert (
        "/workspaces/{workspace_id}"
        "/payroll/runs/{run_id}"
        in paths()
    )


def test_run_summary_route_exists():
    assert (
        "/workspaces/{workspace_id}"
        "/payroll/runs/{run_id}/summary"
        in paths()
    )


def test_router_uses_control_db_for_audit():
    source = inspect.getsource(
        __import__(
            "app.modules.payroll.router",
            fromlist=[
                "router",
            ],
        )
    )

    assert (
        "ControlDB"
        in source
    )

    assert (
        "PayrollAuditService"
        in source
    )


def test_calculate_route_exposed_after_authoritative_wiring():
    """
    Calculation is now intentionally exposed because the
    authoritative backend source assembly is wired.

    Browser input selects employees only. Compensation,
    schedule, attendance, leave, holiday treatment and
    adjustments are resolved by backend services.
    """

    assert (
        "/workspaces/{workspace_id}"
        "/payroll/runs/{run_id}/calculate"
        in paths()
    )