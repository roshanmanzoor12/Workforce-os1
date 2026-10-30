from __future__ import annotations

import inspect

from app.modules.payroll.access_service import (
    PayrollAccessService,
)


def test_access_service_exists():
    assert (
        PayrollAccessService
        is not None
    )


def test_workspace_payroll_uses_canonical_permissions():
    source = inspect.getsource(
        PayrollAccessService
    )

    assert (
        "PAYROLL_READ"
        in source
    )

    assert (
        "PAYROLL_MANAGE"
        in source
    )


def test_self_compensation_uses_self_permission():
    source = inspect.getsource(
        PayrollAccessService
    )

    assert (
        "COMPENSATION_SELF_READ"
        in source
    )


def test_self_scope_resolves_employee_from_user():
    source = inspect.getsource(
        PayrollAccessService
    )

    assert (
        "get_employee_by_user_id"
        in source
    )


def test_generic_employee_visibility_is_not_used():
    source = inspect.getsource(
        PayrollAccessService
    )

    assert (
        "EMPLOYEES_ALL_READ"
        not in source
    )

    assert (
        "EMPLOYEES_TEAM_READ"
        not in source
    )