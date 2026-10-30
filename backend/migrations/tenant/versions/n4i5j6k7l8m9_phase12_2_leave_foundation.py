from __future__ import annotations

from collections.abc import (
    Sequence,
)

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import (
    postgresql,
)


revision: str = (
    "n4i5j6k7l8m9"
)

down_revision: (
    str
    | Sequence[str]
    | None
) = "m3h4i5j6k7l8"

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


leave_request_status = (
    postgresql.ENUM(
        "PENDING",
        "APPROVED",
        "REJECTED",
        "CANCELLED",
        name=(
            "leave_request_status"
        ),
        create_type=False,
    )
)


def upgrade() -> None:
    bind = op.get_bind()

    leave_request_status.create(
        bind,
        checkfirst=True,
    )

    op.create_table(
        "leave_types",

        sa.Column(
            "id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),

        sa.Column(
            "name",
            sa.String(
                length=120
            ),
            nullable=False,
        ),

        sa.Column(
            "code",
            sa.String(
                length=50
            ),
            nullable=False,
        ),

        sa.Column(
            "description",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "is_paid",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),

        sa.Column(
            "requires_approval",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),

        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),

        sa.Column(
            "created_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=False,
            server_default=sa.func.now(),
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=False,
            server_default=sa.func.now(),
        ),

        sa.PrimaryKeyConstraint(
            "id"
        ),

        sa.UniqueConstraint(
            "code",
            name="uq_leave_types_code",
        ),
    )

    op.create_index(
        "ix_leave_types_active",
        "leave_types",
        [
            "is_active",
        ],
        unique=False,
    )

    op.create_table(
        "leave_policies",

        sa.Column(
            "id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),

        sa.Column(
            "leave_type_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),

        sa.Column(
            "annual_allowance_days",
            sa.Numeric(
                8,
                2,
            ),
            nullable=False,
            server_default="0",
        ),

        sa.Column(
            "carry_forward_days",
            sa.Numeric(
                8,
                2,
            ),
            nullable=False,
            server_default="0",
        ),

        sa.Column(
            "minimum_notice_days",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),

        sa.Column(
            "allow_negative_balance",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),

        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),

        sa.Column(
            "created_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=False,
            server_default=sa.func.now(),
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=False,
            server_default=sa.func.now(),
        ),

        sa.ForeignKeyConstraint(
            [
                "leave_type_id",
            ],
            [
                "leave_types.id",
            ],
            ondelete="CASCADE",
        ),

        sa.PrimaryKeyConstraint(
            "id"
        ),

        sa.UniqueConstraint(
            "leave_type_id",
            name=(
                "uq_leave_policies_"
                "leave_type"
            ),
        ),
    )

    op.create_table(
        "leave_balances",

        sa.Column(
            "id",
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
            "leave_type_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),

        sa.Column(
            "balance_year",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "allocated_days",
            sa.Numeric(
                8,
                2,
            ),
            nullable=False,
            server_default="0",
        ),

        sa.Column(
            "carried_forward_days",
            sa.Numeric(
                8,
                2,
            ),
            nullable=False,
            server_default="0",
        ),

        sa.Column(
            "adjustment_days",
            sa.Numeric(
                8,
                2,
            ),
            nullable=False,
            server_default="0",
        ),

        sa.Column(
            "used_days",
            sa.Numeric(
                8,
                2,
            ),
            nullable=False,
            server_default="0",
        ),

        sa.Column(
            "pending_days",
            sa.Numeric(
                8,
                2,
            ),
            nullable=False,
            server_default="0",
        ),

        sa.Column(
            "updated_by_user_id",
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
            server_default=sa.func.now(),
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=False,
            server_default=sa.func.now(),
        ),

        sa.ForeignKeyConstraint(
            [
                "employee_id",
            ],
            [
                "employees.id",
            ],
            ondelete="CASCADE",
        ),

        sa.ForeignKeyConstraint(
            [
                "leave_type_id",
            ],
            [
                "leave_types.id",
            ],
            ondelete="CASCADE",
        ),

        sa.PrimaryKeyConstraint(
            "id"
        ),

        sa.UniqueConstraint(
            "employee_id",
            "leave_type_id",
            "balance_year",
            name=(
                "uq_leave_balances_"
                "employee_type_year"
            ),
        ),
    )

    op.create_index(
        (
            "ix_leave_balances_"
            "employee_year"
        ),
        "leave_balances",
        [
            "employee_id",
            "balance_year",
        ],
        unique=False,
    )

    op.create_table(
        "leave_requests",

        sa.Column(
            "id",
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
            "leave_type_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),

        sa.Column(
            "start_date",
            sa.Date(),
            nullable=False,
        ),

        sa.Column(
            "end_date",
            sa.Date(),
            nullable=False,
        ),

        sa.Column(
            "requested_days",
            sa.Numeric(
                8,
                2,
            ),
            nullable=False,
        ),

        sa.Column(
            "status",
            leave_request_status,
            nullable=False,
        ),

        sa.Column(
            "reason",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "decision_note",
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
            "reviewed_by_user_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=True,
        ),

        sa.Column(
            "reviewed_at",
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
            server_default=sa.func.now(),
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=False,
            server_default=sa.func.now(),
        ),

        sa.ForeignKeyConstraint(
            [
                "employee_id",
            ],
            [
                "employees.id",
            ],
            ondelete="CASCADE",
        ),

        sa.ForeignKeyConstraint(
            [
                "leave_type_id",
            ],
            [
                "leave_types.id",
            ],
            ondelete="RESTRICT",
        ),

        sa.PrimaryKeyConstraint(
            "id"
        ),
    )

    op.create_index(
        (
            "ix_leave_requests_"
            "employee_dates"
        ),
        "leave_requests",
        [
            "employee_id",
            "start_date",
            "end_date",
        ],
        unique=False,
    )

    op.create_index(
        "ix_leave_requests_status",
        "leave_requests",
        [
            "status",
        ],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_leave_requests_status",
        table_name=(
            "leave_requests"
        ),
    )

    op.drop_index(
        (
            "ix_leave_requests_"
            "employee_dates"
        ),
        table_name=(
            "leave_requests"
        ),
    )

    op.drop_table(
        "leave_requests"
    )

    op.drop_index(
        (
            "ix_leave_balances_"
            "employee_year"
        ),
        table_name=(
            "leave_balances"
        ),
    )

    op.drop_table(
        "leave_balances"
    )

    op.drop_table(
        "leave_policies"
    )

    op.drop_index(
        "ix_leave_types_active",
        table_name=(
            "leave_types"
        ),
    )

    op.drop_table(
        "leave_types"
    )

    leave_request_status.drop(
        op.get_bind(),
        checkfirst=True,
    )