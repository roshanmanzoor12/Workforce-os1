from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "o5j6k7l8m9n0"

down_revision: str | None = (
    "n4i5j6k7l8m9"
)

branch_labels: (
    str
    | Sequence[str]
    | None
) = None

depends_on: (
    str
    | Sequence[str]
    | None
) = None


# =========================================================
# ENUMS
# =========================================================


compensation_basis = (
    postgresql.ENUM(
        "MONTHLY",
        "DAILY",
        "HOURLY",
        "FIXED_CONTRACT",
        name="compensation_basis",
        create_type=False,
    )
)


payroll_run_status = (
    postgresql.ENUM(
        "DRAFT",
        "REVIEW",
        "APPROVED",
        "LOCKED",
        "PAID",
        "VOID",
        name="payroll_run_status",
        create_type=False,
    )
)


payroll_calculation_status = (
    postgresql.ENUM(
        "CALCULATED",
        "EXCLUDED",
        name=(
            "payroll_calculation_status"
        ),
        create_type=False,
    )
)


payroll_adjustment_type = (
    postgresql.ENUM(
        "ADDITION",
        "DEDUCTION",
        name=(
            "payroll_adjustment_type"
        ),
        create_type=False,
    )
)


# =========================================================
# UPGRADE
# =========================================================


def upgrade() -> None:
    bind = op.get_bind()

    compensation_basis.create(
        bind,
        checkfirst=True,
    )

    payroll_run_status.create(
        bind,
        checkfirst=True,
    )

    payroll_calculation_status.create(
        bind,
        checkfirst=True,
    )

    payroll_adjustment_type.create(
        bind,
        checkfirst=True,
    )

    # =====================================================
    # COMPENSATION CONTRACTS
    # =====================================================

    op.create_table(
        "compensation_contracts",

        sa.Column(
            "id",
            postgresql.UUID(
                as_uuid=True
            ),
            primary_key=True,
            nullable=False,
        ),

        sa.Column(
            "employee_id",
            postgresql.UUID(
                as_uuid=True
            ),
            sa.ForeignKey(
                "employees.id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),

        sa.Column(
            "basis",
            compensation_basis,
            nullable=False,
        ),

        sa.Column(
            "base_amount",
            sa.Numeric(
                18,
                4,
            ),
            nullable=False,
        ),

        sa.Column(
            "currency",
            sa.String(
                length=3
            ),
            nullable=False,
        ),

        sa.Column(
            "effective_from",
            sa.Date(),
            nullable=False,
        ),

        sa.Column(
            "effective_to",
            sa.Date(),
            nullable=True,
        ),

        sa.Column(
            "standard_day_minutes",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "monthly_divisor_days",
            sa.Numeric(
                10,
                4,
            ),
            nullable=False,
        ),

        sa.Column(
            "overtime_multiplier",
            sa.Numeric(
                8,
                4,
            ),
            nullable=False,
        ),

        sa.Column(
            "overtime_enabled",
            sa.Boolean(),
            nullable=False,
        ),

        sa.Column(
            "notes",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
        ),

        sa.Column(
            "created_by_user_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=True,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=False,
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=False,
        ),

        sa.CheckConstraint(
            "base_amount >= 0",
            name=(
                "ck_compensation_"
                "base_amount_nonnegative"
            ),
        ),

        sa.CheckConstraint(
            (
                "standard_day_minutes "
                "> 0"
            ),
            name=(
                "ck_compensation_"
                "standard_day_minutes_"
                "positive"
            ),
        ),

        sa.CheckConstraint(
            (
                "monthly_divisor_days "
                "> 0"
            ),
            name=(
                "ck_compensation_"
                "monthly_divisor_positive"
            ),
        ),
    )

    op.create_index(
        "ix_compensation_contracts_employee_id",
        "compensation_contracts",
        [
            "employee_id",
        ],
    )

    op.create_index(
        "ix_comp_contract_employee_dates",
        "compensation_contracts",
        [
            "employee_id",
            "effective_from",
            "effective_to",
        ],
    )

    op.create_index(
        "ix_comp_contract_active",
        "compensation_contracts",
        [
            "employee_id",
            "is_active",
        ],
    )

    # =====================================================
    # PAYROLL RUNS
    # =====================================================

    op.create_table(
        "payroll_runs",

        sa.Column(
            "id",
            postgresql.UUID(
                as_uuid=True
            ),
            primary_key=True,
            nullable=False,
        ),

        sa.Column(
            "period_start",
            sa.Date(),
            nullable=False,
        ),

        sa.Column(
            "period_end",
            sa.Date(),
            nullable=False,
        ),

        sa.Column(
            "cutoff_date",
            sa.Date(),
            nullable=True,
        ),

        sa.Column(
            "currency",
            sa.String(
                length=3
            ),
            nullable=False,
        ),

        sa.Column(
            "status",
            payroll_run_status,
            nullable=False,
        ),

        sa.Column(
            "policy_version",
            sa.String(
                length=100
            ),
            nullable=False,
        ),

        sa.Column(
            "notes",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "created_by_user_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=True,
        ),

        sa.Column(
            "approved_by_user_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=True,
        ),

        sa.Column(
            "approved_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=True,
        ),

        sa.Column(
            "locked_by_user_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=True,
        ),

        sa.Column(
            "locked_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=True,
        ),

        sa.Column(
            "paid_by_user_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=True,
        ),

        sa.Column(
            "paid_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=True,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=False,
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=False,
        ),

        sa.UniqueConstraint(
            "period_start",
            "period_end",
            "currency",
            name=(
                "uq_payroll_run_"
                "period_currency"
            ),
        ),

        sa.CheckConstraint(
            (
                "period_end >= "
                "period_start"
            ),
            name=(
                "ck_payroll_run_"
                "period_order"
            ),
        ),
    )

    op.create_index(
        "ix_payroll_run_period",
        "payroll_runs",
        [
            "period_start",
            "period_end",
        ],
    )

    op.create_index(
        "ix_payroll_run_status",
        "payroll_runs",
        [
            "status",
        ],
    )

    # =====================================================
    # CALCULATIONS
    # =====================================================

    op.create_table(
        "payroll_calculations",

        sa.Column(
            "id",
            postgresql.UUID(
                as_uuid=True
            ),
            primary_key=True,
            nullable=False,
        ),

        sa.Column(
            "payroll_run_id",
            postgresql.UUID(
                as_uuid=True
            ),
            sa.ForeignKey(
                "payroll_runs.id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),

        sa.Column(
            "employee_id",
            postgresql.UUID(
                as_uuid=True
            ),
            sa.ForeignKey(
                "employees.id",
                ondelete="RESTRICT",
            ),
            nullable=False,
        ),

        sa.Column(
            "compensation_contract_id",
            postgresql.UUID(
                as_uuid=True
            ),
            sa.ForeignKey(
                (
                    "compensation_contracts"
                    ".id"
                ),
                ondelete="RESTRICT",
            ),
            nullable=False,
        ),

        sa.Column(
            "status",
            payroll_calculation_status,
            nullable=False,
        ),

        sa.Column(
            "currency",
            sa.String(
                length=3
            ),
            nullable=False,
        ),

        sa.Column(
            "base_amount",
            sa.Numeric(
                18,
                4,
            ),
            nullable=False,
        ),

        sa.Column(
            "daily_rate",
            sa.Numeric(
                18,
                6,
            ),
            nullable=False,
        ),

        sa.Column(
            "hourly_rate",
            sa.Numeric(
                18,
                6,
            ),
            nullable=False,
        ),

        sa.Column(
            "minute_rate",
            sa.Numeric(
                18,
                8,
            ),
            nullable=False,
        ),

        sa.Column(
            "scheduled_minutes",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "payable_minutes",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "paid_leave_minutes",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "unpaid_leave_minutes",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "overtime_minutes",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "base_pay",
            sa.Numeric(
                18,
                4,
            ),
            nullable=False,
        ),

        sa.Column(
            "overtime_pay",
            sa.Numeric(
                18,
                4,
            ),
            nullable=False,
        ),

        sa.Column(
            "additions_total",
            sa.Numeric(
                18,
                4,
            ),
            nullable=False,
        ),

        sa.Column(
            "deductions_total",
            sa.Numeric(
                18,
                4,
            ),
            nullable=False,
        ),

        sa.Column(
            "gross_pay",
            sa.Numeric(
                18,
                4,
            ),
            nullable=False,
        ),

        sa.Column(
            "net_pay",
            sa.Numeric(
                18,
                4,
            ),
            nullable=False,
        ),

        sa.Column(
            "source_snapshot",
            postgresql.JSONB(),
            nullable=False,
        ),

        sa.Column(
            "explanation_snapshot",
            postgresql.JSONB(),
            nullable=False,
        ),

        sa.Column(
            "policy_version",
            sa.String(
                length=100
            ),
            nullable=False,
        ),

        sa.Column(
            "calculated_by_user_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=True,
        ),

        sa.Column(
            "calculated_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=False,
        ),

        sa.UniqueConstraint(
            "payroll_run_id",
            "employee_id",
            name=(
                "uq_payroll_calculation_"
                "run_employee"
            ),
        ),

        sa.CheckConstraint(
            "scheduled_minutes >= 0",
            name=(
                "ck_payroll_calc_"
                "scheduled_minutes"
            ),
        ),

        sa.CheckConstraint(
            "payable_minutes >= 0",
            name=(
                "ck_payroll_calc_"
                "payable_minutes"
            ),
        ),

        sa.CheckConstraint(
            "overtime_minutes >= 0",
            name=(
                "ck_payroll_calc_"
                "overtime_minutes"
            ),
        ),

        sa.CheckConstraint(
            (
                "unpaid_leave_minutes "
                ">= 0"
            ),
            name=(
                "ck_payroll_calc_"
                "unpaid_leave_minutes"
            ),
        ),
    )

    op.create_index(
        "ix_payroll_calc_employee",
        "payroll_calculations",
        [
            "employee_id",
        ],
    )

    # =====================================================
    # ADJUSTMENTS
    # =====================================================

    op.create_table(
        "payroll_adjustments",

        sa.Column(
            "id",
            postgresql.UUID(
                as_uuid=True
            ),
            primary_key=True,
            nullable=False,
        ),

        sa.Column(
            "payroll_run_id",
            postgresql.UUID(
                as_uuid=True
            ),
            sa.ForeignKey(
                "payroll_runs.id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),

        sa.Column(
            "employee_id",
            postgresql.UUID(
                as_uuid=True
            ),
            sa.ForeignKey(
                "employees.id",
                ondelete="RESTRICT",
            ),
            nullable=False,
        ),

        sa.Column(
            "adjustment_type",
            payroll_adjustment_type,
            nullable=False,
        ),

        sa.Column(
            "amount",
            sa.Numeric(
                18,
                4,
            ),
            nullable=False,
        ),

        sa.Column(
            "reason",
            sa.String(
                length=500
            ),
            nullable=False,
        ),

        sa.Column(
            "created_by_user_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=False,
        ),

        sa.CheckConstraint(
            "amount > 0",
            name=(
                "ck_payroll_adjustment_"
                "amount_positive"
            ),
        ),
    )

    op.create_index(
        "ix_payroll_adjustment_run",
        "payroll_adjustments",
        [
            "payroll_run_id",
        ],
    )

    op.create_index(
        "ix_payroll_adjustment_employee",
        "payroll_adjustments",
        [
            "employee_id",
        ],
    )


# =========================================================
# DOWNGRADE
# =========================================================


def downgrade() -> None:
    op.drop_index(
        "ix_payroll_adjustment_employee",
        table_name=(
            "payroll_adjustments"
        ),
    )

    op.drop_index(
        "ix_payroll_adjustment_run",
        table_name=(
            "payroll_adjustments"
        ),
    )

    op.drop_table(
        "payroll_adjustments"
    )

    op.drop_index(
        "ix_payroll_calc_employee",
        table_name=(
            "payroll_calculations"
        ),
    )

    op.drop_table(
        "payroll_calculations"
    )

    op.drop_index(
        "ix_payroll_run_status",
        table_name="payroll_runs",
    )

    op.drop_index(
        "ix_payroll_run_period",
        table_name="payroll_runs",
    )

    op.drop_table(
        "payroll_runs"
    )

    op.drop_index(
        "ix_comp_contract_active",
        table_name=(
            "compensation_contracts"
        ),
    )

    op.drop_index(
        "ix_comp_contract_employee_dates",
        table_name=(
            "compensation_contracts"
        ),
    )

    op.drop_index(
        (
            "ix_compensation_"
            "contracts_employee_id"
        ),
        table_name=(
            "compensation_contracts"
        ),
    )

    op.drop_table(
        "compensation_contracts"
    )

    bind = op.get_bind()

    payroll_adjustment_type.drop(
        bind,
        checkfirst=True,
    )

    payroll_calculation_status.drop(
        bind,
        checkfirst=True,
    )

    payroll_run_status.drop(
        bind,
        checkfirst=True,
    )

    compensation_basis.drop(
        bind,
        checkfirst=True,
    )