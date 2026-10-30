from __future__ import annotations

import inspect

from app.modules.payroll.audit import (
    PAYROLL_AUDIT_CATEGORY,
    PayrollAuditService,
)


def test_payroll_audit_category():
    assert (
        PAYROLL_AUDIT_CATEGORY
        == "payroll"
    )


def test_payroll_audit_uses_control_audit_service():
    source = inspect.getsource(
        PayrollAuditService
    )

    assert (
        "AuditLogService"
        in source
    )

    assert (
        "AuditEventCreate"
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
        "payroll.adjustment.created",
        "payroll.run.approved",
        "payroll.run.locked",
        "payroll.run.paid",
    }

    for action in required:
        assert action in source


def test_audit_does_not_store_salary_amount():
    source = inspect.getsource(
        PayrollAuditService
    )

    assert (
        '"base_amount"'
        not in source
    )

    assert (
        '"net_pay"'
        not in source
    )

    assert (
        '"gross_pay"'
        not in source
    )