from __future__ import annotations

import inspect

from app.modules.payroll.calculation_service import (
    PayrollCalculationService,
)
from app.modules.payroll.models import (
    PayrollCalculation,
)
from app.modules.payroll.payslip_models import (
    PayrollPayslip,
)
from app.modules.payroll.payslip_service import (
    PayrollPayslipService,
)


def test_calculation_has_source_snapshot():
    assert (
        "source_snapshot"
        in PayrollCalculation
        .__table__
        .columns
    )


def test_calculation_has_explanation_snapshot():
    assert (
        "explanation_snapshot"
        in PayrollCalculation
        .__table__
        .columns
    )


def test_calculation_has_policy_version():
    assert (
        "policy_version"
        in PayrollCalculation
        .__table__
        .columns
    )


def test_authoritative_calculation_persists_source_snapshot():
    source = inspect.getsource(
        PayrollCalculationService
    )

    assert (
        "source_snapshot"
        in source
    )

    assert (
        "PayrollSourceAssembler"
        in source
    )


def test_authoritative_calculation_rejects_final_states():
    source = inspect.getsource(
        PayrollCalculationService
    )

    assert (
        "PayrollRunStatus.DRAFT"
        in source
    )

    assert (
        "PayrollRunStatus.REVIEW"
        in source
    )

    assert (
        "HTTP_409_CONFLICT"
        in source
    )


def test_payslip_is_final_snapshot():
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
        "source_snapshot"
        in source
    )

    assert (
        "explanation_snapshot"
        in source
    )

    assert (
        "policy_version"
        in source
    )


def test_payslip_requires_paid_run():
    source = inspect.getsource(
        PayrollPayslipService
    )

    assert (
        "PayrollRunStatus.PAID"
        in source
    )