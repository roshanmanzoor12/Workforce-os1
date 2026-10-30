from __future__ import annotations

import inspect

from app.modules.payroll.payslip_models import (
    PayrollPayslip,
)
from app.modules.payroll.payslip_router import (
    router,
)
from app.modules.payroll.payslip_service import (
    PayrollPayslipService,
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


def test_payslip_table_name():
    assert (
        PayrollPayslip.__tablename__
        == "payroll_payslips"
    )


def test_self_payslip_route():
    assert (
        "/workspaces/{workspace_id}"
        "/payroll/me/payslips"
        in paths()
    )


def test_payslip_detail_route():
    assert (
        "/workspaces/{workspace_id}"
        "/payroll/payslips/{payslip_id}"
        in paths()
    )


def test_publish_route():
    assert (
        "/workspaces/{workspace_id}"
        "/payroll/runs/{run_id}"
        "/payslips/publish"
        in paths()
    )


def test_publish_requires_paid_run():
    source = inspect.getsource(
        PayrollPayslipService
    )

    assert (
        "PayrollRunStatus.PAID"
        in source
    )

    assert (
        "HTTP_409_CONFLICT"
        in source
    )


def test_payslip_stores_snapshot():
    assert (
        "statement_snapshot"
        in PayrollPayslip.__table__.columns
    )


def test_payslip_run_employee_unique():
    constraints = {
        constraint.name
        for constraint
        in PayrollPayslip
        .__table__
        .constraints
    }

    assert (
        "uq_payroll_payslip_run_employee"
        in constraints
    )


def test_payslip_has_calculation_reference():
    assert (
        "payroll_calculation_id"
        in PayrollPayslip
        .__table__
        .columns
    )