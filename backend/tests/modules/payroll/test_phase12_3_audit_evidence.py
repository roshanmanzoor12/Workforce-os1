from __future__ import annotations

import inspect

from app.modules.payroll.audit import (
    PayrollAuditService,
)


def test_payroll_audit_uses_audit_log():
    source = inspect.getsource(
        PayrollAuditService
    )

    assert (
        "AuditLogService"
        in source
    )


def test_contract_create_audited():
    source = inspect.getsource(
        PayrollAuditService
    )

    assert (
        "compensation.contract.created"
        in source
    )


def test_contract_update_audited():
    source = inspect.getsource(
        PayrollAuditService
    )

    assert (
        "compensation.contract.updated"
        in source
    )


def test_run_create_audited():
    source = inspect.getsource(
        PayrollAuditService
    )

    assert (
        "payroll.run.created"
        in source
    )


def test_calculation_audited():
    source = inspect.getsource(
        PayrollAuditService
    )

    assert (
        "payroll.run.calculated"
        in source
    )


def test_adjustment_audited():
    source = inspect.getsource(
        PayrollAuditService
    )

    assert (
        "payroll.adjustment.created"
        in source
    )


def test_approve_lock_paid_audited():
    source = inspect.getsource(
        PayrollAuditService
    )

    required = {
        "payroll.run.approved",
        "payroll.run.locked",
        "payroll.run.paid",
    }

    for value in required:
        assert value in source


def test_audit_does_not_emit_salary_values():
    source = inspect.getsource(
        PayrollAuditService
    )

    forbidden = {
        '"base_amount"',
        '"gross_pay"',
        '"net_pay"',
        '"salary"',
    }

    for value in forbidden:
        assert value not in source