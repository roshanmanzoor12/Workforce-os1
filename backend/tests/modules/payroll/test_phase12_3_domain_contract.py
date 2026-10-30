from __future__ import annotations

from app.db.tenant_base import (
    TenantBase,
)
from app.modules.payroll.models import (
    CompensationBasis,
    CompensationContract,
    PayrollAdjustment,
    PayrollAdjustmentType,
    PayrollCalculation,
    PayrollCalculationStatus,
    PayrollRun,
    PayrollRunStatus,
)
from app.modules.payroll.permissions import (
    ALL_PAYROLL_PERMISSIONS,
)


def test_compensation_basis_values():
    assert {
        item.value
        for item in CompensationBasis
    } == {
        "monthly",
        "daily",
        "hourly",
        "fixed_contract",
    }


def test_payroll_run_status_flow():
    assert {
        item.value
        for item in PayrollRunStatus
    } == {
        "draft",
        "review",
        "approved",
        "locked",
        "paid",
        "void",
    }


def test_adjustment_types():
    assert {
        item.value
        for item
        in PayrollAdjustmentType
    } == {
        "addition",
        "deduction",
    }


def test_calculation_statuses():
    assert {
        item.value
        for item
        in PayrollCalculationStatus
    } == {
        "calculated",
        "excluded",
    }


def test_payroll_model_tables():
    assert (
        CompensationContract
        .__tablename__
        == "compensation_contracts"
    )

    assert (
        PayrollRun.__tablename__
        == "payroll_runs"
    )

    assert (
        PayrollCalculation
        .__tablename__
        == "payroll_calculations"
    )

    assert (
        PayrollAdjustment
        .__tablename__
        == "payroll_adjustments"
    )


def test_tables_registered_in_tenant_metadata():
    tables = set(
        TenantBase.metadata.tables
    )

    assert {
        "compensation_contracts",
        "payroll_runs",
        "payroll_calculations",
        "payroll_adjustments",
    } <= tables


def test_salary_belongs_to_employee():
    columns = {
        column.name
        for column
        in CompensationContract
        .__table__
        .columns
    }

    assert "employee_id" in columns
    assert "role_id" not in columns
    assert "role_key" not in columns


def test_calculation_has_immutable_source_snapshot():
    columns = {
        column.name
        for column
        in PayrollCalculation
        .__table__
        .columns
    }

    assert (
        "source_snapshot"
        in columns
    )

    assert (
        "explanation_snapshot"
        in columns
    )

    assert (
        "policy_version"
        in columns
    )


def test_adjustment_has_reason_and_actor():
    columns = {
        column.name
        for column
        in PayrollAdjustment
        .__table__
        .columns
    }

    assert "reason" in columns

    assert (
        "created_by_user_id"
        in columns
    )


def test_permission_catalog_foundation():
    required = {
        "payroll.view",
        "payroll.run",
        "payroll.edit",
        "payroll.approve",
        "payroll.lock",
        "payroll.mark_paid",
        "compensation.view",
        "compensation.manage",
    }

    assert (
        required
        <= ALL_PAYROLL_PERMISSIONS
    )