from __future__ import annotations

from alembic import op
import sqlalchemy as sa

from sqlalchemy.dialects import (
    postgresql,
)


revision = (
    "p6k7l8m9n0o1"
)

down_revision = (
    "o5j6k7l8m9n0"
)

branch_labels = None

depends_on = None


def upgrade() -> None:
    op.create_table(
        "payroll_payslips",

        sa.Column(
            "id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),

        sa.Column(
            "payroll_run_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),

        sa.Column(
            "payroll_calculation_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),

        sa.Column(
            "employee_id",
            postgresql.UUID(
                as_uuid=True
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
            "gross_pay",
            sa.Numeric(
                precision=18,
                scale=4,
            ),
            nullable=False,
        ),

        sa.Column(
            "additions_total",
            sa.Numeric(
                precision=18,
                scale=4,
            ),
            nullable=False,
        ),

        sa.Column(
            "deductions_total",
            sa.Numeric(
                precision=18,
                scale=4,
            ),
            nullable=False,
        ),

        sa.Column(
            "net_pay",
            sa.Numeric(
                precision=18,
                scale=4,
            ),
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
            "statement_snapshot",
            postgresql.JSONB(
                astext_type=sa.Text()
            ),
            nullable=False,
        ),

        sa.Column(
            "published_by_user_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),

        sa.Column(
            "published_at",
            sa.DateTime(
                timezone=True
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

        sa.ForeignKeyConstraint(
            [
                "employee_id",
            ],
            [
                "employees.id",
            ],
            name=(
                "fk_payroll_payslips_"
                "employee"
            ),
            ondelete="RESTRICT",
        ),

        sa.ForeignKeyConstraint(
            [
                "payroll_calculation_id",
            ],
            [
                "payroll_calculations.id",
            ],
            name=(
                "fk_payroll_payslips_"
                "calculation"
            ),
            ondelete="RESTRICT",
        ),

        sa.ForeignKeyConstraint(
            [
                "payroll_run_id",
            ],
            [
                "payroll_runs.id",
            ],
            name=(
                "fk_payroll_payslips_run"
            ),
            ondelete="RESTRICT",
        ),

        sa.PrimaryKeyConstraint(
            "id",
            name=(
                "pk_payroll_payslips"
            ),
        ),

        sa.UniqueConstraint(
            "payroll_run_id",
            "employee_id",
            name=(
                "uq_payroll_payslip_"
                "run_employee"
            ),
        ),
    )

    op.create_index(
        "ix_payroll_payslips_employee",
        "payroll_payslips",
        [
            "employee_id",
            "published_at",
        ],
        unique=False,
    )

    op.create_index(
        "ix_payroll_payslips_run",
        "payroll_payslips",
        [
            "payroll_run_id",
        ],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_payroll_payslips_run",
        table_name=(
            "payroll_payslips"
        ),
    )

    op.drop_index(
        "ix_payroll_payslips_employee",
        table_name=(
            "payroll_payslips"
        ),
    )

    op.drop_table(
        "payroll_payslips"
    )