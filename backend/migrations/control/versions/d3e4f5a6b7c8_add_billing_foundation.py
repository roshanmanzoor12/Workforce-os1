"""add billing foundation

Revision ID: d3e4f5a6b7c8
Revises: None
Create Date: 2026-09-03

IMPORTANT:
If your current CONTROL migration head is not None,
replace down_revision below with the actual current
control-database Alembic revision before running upgrade.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = (
    "d3e4f5a6b7c8"
)

down_revision: str | None = "d82af39c61e7"

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


def upgrade() -> None:
    op.create_table(
        "billing_customers",

        sa.Column(
            "id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),

        sa.Column(
            "user_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),

        sa.Column(
            "provider",
            sa.String(
                length=32
            ),
            nullable=False,
            server_default="none",
        ),

        sa.Column(
            "provider_customer_id",
            sa.String(
                length=255
            ),
            nullable=True,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=False,
            server_default=sa.text(
                "CURRENT_TIMESTAMP"
            ),
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=False,
            server_default=sa.text(
                "CURRENT_TIMESTAMP"
            ),
        ),

        sa.PrimaryKeyConstraint(
            "id",
            name="pk_billing_customers",
        ),

        sa.UniqueConstraint(
            "user_id",
            name="uq_billing_customers_user_id",
        ),

        sa.UniqueConstraint(
            "provider_customer_id",
            name=(
                "uq_billing_customers_"
                "provider_customer_id"
            ),
        ),
    )

    op.create_index(
        "ix_billing_customers_user_id",
        "billing_customers",
        [
            "user_id",
        ],
        unique=True,
    )

    op.create_table(
        "billing_subscriptions",

        sa.Column(
            "id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),

        sa.Column(
            "user_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),

        sa.Column(
            "plan_code",
            sa.String(
                length=32
            ),
            nullable=False,
            server_default="free",
        ),

        sa.Column(
            "provider",
            sa.String(
                length=32
            ),
            nullable=False,
            server_default="none",
        ),

        sa.Column(
            "provider_subscription_id",
            sa.String(
                length=255
            ),
            nullable=True,
        ),

        sa.Column(
            "status",
            sa.String(
                length=32
            ),
            nullable=False,
            server_default="none",
        ),

        sa.Column(
            "current_period_start",
            sa.DateTime(
                timezone=True
            ),
            nullable=True,
        ),

        sa.Column(
            "current_period_end",
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
            server_default=sa.text(
                "CURRENT_TIMESTAMP"
            ),
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=False,
            server_default=sa.text(
                "CURRENT_TIMESTAMP"
            ),
        ),

        sa.PrimaryKeyConstraint(
            "id",
            name="pk_billing_subscriptions",
        ),

        sa.UniqueConstraint(
            "user_id",
            name=(
                "uq_billing_subscription_user"
            ),
        ),

        sa.UniqueConstraint(
            "provider_subscription_id",
            name=(
                "uq_billing_subscriptions_"
                "provider_subscription_id"
            ),
        ),
    )

    op.create_index(
        "ix_billing_subscriptions_user_id",
        "billing_subscriptions",
        [
            "user_id",
        ],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_billing_subscriptions_user_id",
        table_name="billing_subscriptions",
    )

    op.drop_table(
        "billing_subscriptions"
    )

    op.drop_index(
        "ix_billing_customers_user_id",
        table_name="billing_customers",
    )

    op.drop_table(
        "billing_customers"
    )
