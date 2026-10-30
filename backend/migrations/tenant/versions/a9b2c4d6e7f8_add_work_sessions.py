from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "a9b2c4d6e7f8"

down_revision: str | None = "f8a1c3d4e5b6"

branch_labels: Sequence[str] | None = None

depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "work_sessions",
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
            "status",
            sa.String(
                length=20
            ),
            nullable=False,
        ),
        sa.Column(
            "current_state",
            sa.String(
                length=20
            ),
            nullable=False,
        ),
        sa.Column(
            "started_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=False,
        ),
        sa.Column(
            "ended_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=True,
        ),
        sa.Column(
            "last_observed_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=False,
        ),
        sa.Column(
            "active_seconds",
            sa.Integer(),
            nullable=False,
            server_default=sa.text(
                "0"
            ),
        ),
        sa.Column(
            "idle_seconds",
            sa.Integer(),
            nullable=False,
            server_default=sa.text(
                "0"
            ),
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
        sa.CheckConstraint(
            "status IN ('open', 'closed')",
            name="ck_work_sessions_status",
        ),
        sa.CheckConstraint(
            "current_state IN ('active', 'idle')",
            name="ck_work_sessions_current_state",
        ),
        sa.CheckConstraint(
            "active_seconds >= 0",
            name="ck_work_sessions_active_seconds_nonnegative",
        ),
        sa.CheckConstraint(
            "idle_seconds >= 0",
            name="ck_work_sessions_idle_seconds_nonnegative",
        ),
        sa.CheckConstraint(
            "ended_at IS NULL OR ended_at >= started_at",
            name="ck_work_sessions_valid_time_range",
        ),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["devices.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["employee_id"],
            ["employees.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint(
            "id"
        ),
    )

    op.create_index(
        "ix_work_sessions_device_started_at",
        "work_sessions",
        [
            "device_id",
            "started_at",
        ],
        unique=False,
    )

    op.create_index(
        "ix_work_sessions_employee_started_at",
        "work_sessions",
        [
            "employee_id",
            "started_at",
        ],
        unique=False,
    )

    op.create_index(
        "ix_work_sessions_status_last_observed_at",
        "work_sessions",
        [
            "status",
            "last_observed_at",
        ],
        unique=False,
    )

    op.create_index(
        "uq_work_sessions_one_open_per_device",
        "work_sessions",
        [
            "device_id",
        ],
        unique=True,
        postgresql_where=sa.text(
            "status = 'open'"
        ),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_work_sessions_one_open_per_device",
        table_name="work_sessions",
    )

    op.drop_index(
        "ix_work_sessions_status_last_observed_at",
        table_name="work_sessions",
    )

    op.drop_index(
        "ix_work_sessions_employee_started_at",
        table_name="work_sessions",
    )

    op.drop_index(
        "ix_work_sessions_device_started_at",
        table_name="work_sessions",
    )

    op.drop_table(
        "work_sessions"
    )