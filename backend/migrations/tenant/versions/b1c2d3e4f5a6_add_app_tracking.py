from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "b1c2d3e4f5a6"

down_revision: str | None = "a9b2c4d6e7f8"

branch_labels: Sequence[str] | None = None

depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "app_observations",
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
            "app_key",
            sa.String(
                length=64
            ),
            nullable=False,
        ),
        sa.Column(
            "process_name",
            sa.String(
                length=255
            ),
            nullable=False,
        ),
        sa.Column(
            "executable_path",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "window_title",
            sa.Text(),
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
            server_default=sa.text(
                "CURRENT_TIMESTAMP"
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
        "ix_app_observations_device_observed_at",
        "app_observations",
        [
            "device_id",
            "observed_at",
        ],
        unique=False,
    )

    op.create_index(
        "ix_app_observations_employee_observed_at",
        "app_observations",
        [
            "employee_id",
            "observed_at",
        ],
        unique=False,
    )

    op.create_index(
        "ix_app_observations_app_key_observed_at",
        "app_observations",
        [
            "app_key",
            "observed_at",
        ],
        unique=False,
    )

    op.create_table(
        "app_usage_intervals",
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
            "app_key",
            sa.String(
                length=64
            ),
            nullable=False,
        ),
        sa.Column(
            "process_name",
            sa.String(
                length=255
            ),
            nullable=False,
        ),
        sa.Column(
            "executable_path",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "last_window_title",
            sa.Text(),
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
            "duration_seconds",
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
            name="ck_app_usage_intervals_status",
        ),
        sa.CheckConstraint(
            "duration_seconds >= 0",
            name="ck_app_usage_intervals_duration_nonnegative",
        ),
        sa.CheckConstraint(
            "ended_at IS NULL OR ended_at >= started_at",
            name="ck_app_usage_intervals_valid_time_range",
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
        "ix_app_usage_intervals_device_started_at",
        "app_usage_intervals",
        [
            "device_id",
            "started_at",
        ],
        unique=False,
    )

    op.create_index(
        "ix_app_usage_intervals_employee_started_at",
        "app_usage_intervals",
        [
            "employee_id",
            "started_at",
        ],
        unique=False,
    )

    op.create_index(
        "ix_app_usage_intervals_app_key_started_at",
        "app_usage_intervals",
        [
            "app_key",
            "started_at",
        ],
        unique=False,
    )

    op.create_index(
        "uq_app_usage_one_open_per_device",
        "app_usage_intervals",
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
        "uq_app_usage_one_open_per_device",
        table_name="app_usage_intervals",
    )

    op.drop_index(
        "ix_app_usage_intervals_app_key_started_at",
        table_name="app_usage_intervals",
    )

    op.drop_index(
        "ix_app_usage_intervals_employee_started_at",
        table_name="app_usage_intervals",
    )

    op.drop_index(
        "ix_app_usage_intervals_device_started_at",
        table_name="app_usage_intervals",
    )

    op.drop_table(
        "app_usage_intervals"
    )

    op.drop_index(
        "ix_app_observations_app_key_observed_at",
        table_name="app_observations",
    )

    op.drop_index(
        "ix_app_observations_employee_observed_at",
        table_name="app_observations",
    )

    op.drop_index(
        "ix_app_observations_device_observed_at",
        table_name="app_observations",
    )

    op.drop_table(
        "app_observations"
    )