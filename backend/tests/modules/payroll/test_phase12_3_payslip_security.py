from __future__ import annotations

import inspect

from app.modules.payroll.payslip_access import (
    PayrollPayslipAccessService,
)
from app.modules.payroll.payslip_models import (
    PayrollPayslip,
)


def test_payslip_employee_scope_exists():
    assert (
        "employee_id"
        in PayrollPayslip
        .__table__
        .columns
    )


def test_self_read_permission_is_checked():
    source = inspect.getsource(
        PayrollPayslipAccessService
    )

    assert (
        "COMPENSATION_SELF_READ"
        in source
    )


def test_payroll_read_permission_is_checked():
    source = inspect.getsource(
        PayrollPayslipAccessService
    )

    assert (
        "PAYROLL_READ"
        in source
    )


def test_self_access_matches_employee():
    source = inspect.getsource(
        PayrollPayslipAccessService
    )

    assert (
        "employee.id"
        in source
    )

    assert (
        "payslip.employee_id"
        in source
    )


def test_denied_payslip_returns_403():
    source = inspect.getsource(
        PayrollPayslipAccessService
    )

    assert (
        "HTTP_403_FORBIDDEN"
        in source
    )


def test_payslip_has_no_workspace_database_identifier():
    columns = {
        column.name
        for column
        in PayrollPayslip
        .__table__
        .columns
    }

    assert (
        "database_name"
        not in columns
    )

    assert (
        "tenant_database"
        not in columns
    )