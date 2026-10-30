from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


__all__ = [
    "upgrade",
    "downgrade",
]


# Alembic identifiers
revision: str = "f8a1c3d4e5b6"
down_revision: str | None = "c5e4d7a91b26"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "activity_state_events",
        sa.Column(
            "id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),
        sa.Column(
            "device_id",
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
            nullable=True,
        ),
        sa.Column(
            "state",
            sa.String(
                length=20
            ),
            nullable=False,
        ),
        sa.Column(
            "idle_seconds",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "last_input_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=True,
        ),
        sa.Column(
            "observed_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=False,
        ),
        sa.Column(
            "received_at",
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
        sa.CheckConstraint(
            "state IN ('active', 'idle')",
            name=(
                "ck_activity_state_events_state"
            ),
        ),
        sa.CheckConstraint(
            "idle_seconds >= 0",
            name=(
                "ck_activity_state_events_"
                "idle_seconds_nonnegative"
            ),
        ),
        sa.ForeignKeyConstraint(
            [
                "device_id",
            ],
            [
                "devices.id",
            ],
            name=(
                "fk_activity_state_events_"
                "device_id_devices"
            ),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            [
                "employee_id",
            ],
            [
                "employees.id",
            ],
            name=(
                "fk_activity_state_events_"
                "employee_id_employees"
            ),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name=(
                "pk_activity_state_events"
            ),
        ),
    )

    op.create_index(
        "ix_activity_state_events_device_observed_at",
        "activity_state_events",
        [
            "device_id",
            "observed_at",
        ],
        unique=False,
    )

    op.create_index(
        "ix_activity_state_events_employee_observed_at",
        "activity_state_events",
        [
            "employee_id",
            "observed_at",
        ],
        unique=False,
    )

    op.create_index(
        "ix_activity_state_events_received_at",
        "activity_state_events",
        [
            "received_at",
        ],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_activity_state_events_received_at",
        table_name="activity_state_events",
    )

    op.drop_index(
        "ix_activity_state_events_employee_observed_at",
        table_name="activity_state_events",
    )

    op.drop_index(
        "ix_activity_state_events_device_observed_at",
        table_name="activity_state_events",
    )

    op.drop_table(
        "activity_state_events"
    )