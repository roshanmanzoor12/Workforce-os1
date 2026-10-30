from __future__ import annotations

from app.modules.payroll.router import (
    router as payroll_router,
)
from app.modules.payroll.payslip_router import (
    router as payslip_router,
)


def _paths(
    router,
) -> set[str]:
    return {
        route.path
        for route in router.routes
        if hasattr(
            route,
            "path",
        )
    }


def test_required_payroll_api_contract():
    paths = _paths(
        payroll_router
    )

    required = {
        (
            "/workspaces/{workspace_id}"
            "/compensation/contracts"
        ),
        (
            "/workspaces/{workspace_id}"
            "/compensation/contracts/"
            "{contract_id}"
        ),
        (
            "/workspaces/{workspace_id}"
            "/payroll/runs"
        ),
        (
            "/workspaces/{workspace_id}"
            "/payroll/runs/{run_id}"
            "/calculate"
        ),
        (
            "/workspaces/{workspace_id}"
            "/payroll/runs/{run_id}"
            "/employees"
        ),
        (
            "/workspaces/{workspace_id}"
            "/payroll/runs/{run_id}"
            "/adjustments"
        ),
        (
            "/workspaces/{workspace_id}"
            "/payroll/runs/{run_id}"
            "/approve"
        ),
        (
            "/workspaces/{workspace_id}"
            "/payroll/runs/{run_id}"
            "/lock"
        ),
        (
            "/workspaces/{workspace_id}"
            "/payroll/runs/{run_id}"
            "/mark-paid"
        ),
    }

    assert required <= paths


def test_required_payslip_api_contract():
    paths = _paths(
        payslip_router
    )

    assert (
        "/workspaces/{workspace_id}"
        "/payroll/me/payslips"
        in paths
    )

    assert (
        "/workspaces/{workspace_id}"
        "/payroll/payslips/"
        "{payslip_id}"
        in paths
    )


def test_calculate_is_post():
    target = (
        "/workspaces/{workspace_id}"
        "/payroll/runs/{run_id}"
        "/calculate"
    )

    matches = [
        route
        for route
        in payroll_router.routes
        if getattr(
            route,
            "path",
            None,
        )
        == target
    ]

    assert len(
        matches
    ) == 1

    assert (
        "POST"
        in matches[0].methods
    )


def test_payroll_employee_rows_are_get():
    target = (
        "/workspaces/{workspace_id}"
        "/payroll/runs/{run_id}"
        "/employees"
    )

    matches = [
        route
        for route
        in payroll_router.routes
        if getattr(
            route,
            "path",
            None,
        )
        == target
    ]

    assert len(
        matches
    ) == 1

    assert (
        "GET"
        in matches[0].methods
    )