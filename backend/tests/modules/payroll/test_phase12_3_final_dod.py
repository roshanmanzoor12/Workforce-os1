from __future__ import annotations

import inspect

from app.db.tenant_initialization import (
    CURRENT_TENANT_SCHEMA_VERSION,
)
from app.modules.payroll.audit import (
    PayrollAuditService,
)
from app.modules.payroll.calculation_service import (
    PayrollCalculationService,
)
from app.modules.payroll.payslip_access import (
    PayrollPayslipAccessService,
)
from app.modules.payroll.payslip_models import (
    PayrollPayslip,
)
from app.modules.payroll.payslip_service import (
    PayrollPayslipService,
)
from app.modules.payroll.router import (
    router as payroll_router,
)
from app.modules.payroll.payslip_router import (
    router as payslip_router,
)


EXPECTED_HEAD = (
    "p6k7l8m9n0o1"
)


def _all_paths() -> set[str]:
    result = set()

    for router in (
        payroll_router,
        payslip_router,
    ):
        result.update(
            route.path
            for route
            in router.routes
            if hasattr(
                route,
                "path",
            )
        )

    return result


def test_runtime_schema_head():
    assert (
        CURRENT_TENANT_SCHEMA_VERSION
        == EXPECTED_HEAD
    )


def test_required_backend_api_complete():
    paths = _all_paths()

    required = {
        (
            "/workspaces/{workspace_id}"
            "/compensation/contracts"
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
        (
            "/workspaces/{workspace_id}"
            "/payroll/me/payslips"
        ),
        (
            "/workspaces/{workspace_id}"
            "/payroll/payslips/"
            "{payslip_id}"
        ),
    }

    assert required <= paths


def test_backend_is_calculation_authority():
    source = inspect.getsource(
        PayrollCalculationService
    )

    assert (
        "PayrollSourceAssembler"
        in source
    )

    assert (
        "source_snapshot"
        in source
    )


def test_final_payslip_is_snapshot():
    assert (
        "statement_snapshot"
        in PayrollPayslip
        .__table__
        .columns
    )

    source = inspect.getsource(
        PayrollPayslipService
    )

    assert (
        "PayrollRunStatus.PAID"
        in source
    )


def test_payslip_has_self_scope_enforcement():
    source = inspect.getsource(
        PayrollPayslipAccessService
    )

    assert (
        "COMPENSATION_SELF_READ"
        in source
    )

    assert (
        "employee.id"
        in source
    )

    assert (
        "payslip.employee_id"
        in source
    )


def test_sensitive_actions_are_audited():
    source = inspect.getsource(
        PayrollAuditService
    )

    required = {
        "compensation.contract.created",
        "compensation.contract.updated",
        "payroll.run.created",
        "payroll.run.calculated",
        "payroll.adjustment.created",
        "payroll.run.approved",
        "payroll.run.locked",
        "payroll.run.paid",
    }

    for value in required:
        assert value in source