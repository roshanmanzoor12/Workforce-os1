from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "c2d3e4f5a6b7"
down_revision = "b1c2d3e4f5a6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "website_observations",

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
            "browser_name",
            sa.String(
                length=100
            ),
            nullable=False,
        ),

        sa.Column(
            "browser_process_name",
            sa.String(
                length=255
            ),
            nullable=False,
        ),

        sa.Column(
            "domain",
            sa.String(
                length=255
            ),
            nullable=False,
        ),

        sa.Column(
            "normalized_domain",
            sa.String(
                length=255
            ),
            nullable=False,
        ),

        sa.Column(
            "page_url",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "page_title",
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
            server_default=sa.text(
                "CURRENT_TIMESTAMP"
            ),
            nullable=False,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(
                timezone=True
            ),
            server_default=sa.text(
                "CURRENT_TIMESTAMP"
            ),
            nullable=False,
        ),

        sa.ForeignKeyConstraint(
            [
                "device_id"
            ],
            [
                "devices.id"
            ],
            ondelete="CASCADE",
        ),

        sa.ForeignKeyConstraint(
            [
                "employee_id"
            ],
            [
                "employees.id"
            ],
            ondelete="SET NULL",
        ),

        sa.PrimaryKeyConstraint(
            "id"
        ),
    )

    op.create_index(
        "ix_website_observations_device_observed_at",
        "website_observations",
        [
            "device_id",
            "observed_at",
        ],
        unique=False,
    )

    op.create_index(
        "ix_website_observations_employee_observed_at",
        "website_observations",
        [
            "employee_id",
            "observed_at",
        ],
        unique=False,
    )

    op.create_index(
        "ix_website_observations_domain_observed_at",
        "website_observations",
        [
            "normalized_domain",
            "observed_at",
        ],
        unique=False,
    )

    op.create_table(
        "website_usage_intervals",

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
            "browser_name",
            sa.String(
                length=100
            ),
            nullable=False,
        ),

        sa.Column(
            "browser_process_name",
            sa.String(
                length=255
            ),
            nullable=False,
        ),

        sa.Column(
            "domain",
            sa.String(
                length=255
            ),
            nullable=False,
        ),

        sa.Column(
            "normalized_domain",
            sa.String(
                length=255
            ),
            nullable=False,
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
        ),

        sa.Column(
            "last_page_url",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "last_page_title",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(
                timezone=True
            ),
            server_default=sa.text(
                "CURRENT_TIMESTAMP"
            ),
            nullable=False,
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(
                timezone=True
            ),
            server_default=sa.text(
                "CURRENT_TIMESTAMP"
            ),
            nullable=False,
        ),

        sa.CheckConstraint(
            "status IN ('open', 'closed')",
            name=(
                "ck_website_usage_intervals_status"
            ),
        ),

        sa.CheckConstraint(
            "duration_seconds >= 0",
            name=(
                "ck_website_usage_intervals_duration_nonnegative"
            ),
        ),

        sa.CheckConstraint(
            (
                "ended_at IS NULL "
                "OR ended_at >= started_at"
            ),
            name=(
                "ck_website_usage_intervals_valid_time_range"
            ),
        ),

        sa.ForeignKeyConstraint(
            [
                "device_id"
            ],
            [
                "devices.id"
            ],
            ondelete="CASCADE",
        ),

        sa.ForeignKeyConstraint(
            [
                "employee_id"
            ],
            [
                "employees.id"
            ],
            ondelete="SET NULL",
        ),

        sa.PrimaryKeyConstraint(
            "id"
        ),
    )

    op.create_index(
        "ix_website_usage_intervals_device_started_at",
        "website_usage_intervals",
        [
            "device_id",
            "started_at",
        ],
        unique=False,
    )

    op.create_index(
        "ix_website_usage_intervals_employee_started_at",
        "website_usage_intervals",
        [
            "employee_id",
            "started_at",
        ],
        unique=False,
    )

    op.create_index(
        "ix_website_usage_intervals_domain_started_at",
        "website_usage_intervals",
        [
            "normalized_domain",
            "started_at",
        ],
        unique=False,
    )

    op.create_index(
        "uq_website_usage_one_open_per_device",
        "website_usage_intervals",
        [
            "device_id"
        ],
        unique=True,
        postgresql_where=sa.text(
            "status = 'open'"
        ),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_website_usage_one_open_per_device",
        table_name="website_usage_intervals",
    )

    op.drop_index(
        "ix_website_usage_intervals_domain_started_at",
        table_name="website_usage_intervals",
    )

    op.drop_index(
        "ix_website_usage_intervals_employee_started_at",
        table_name="website_usage_intervals",
    )

    op.drop_index(
        "ix_website_usage_intervals_device_started_at",
        table_name="website_usage_intervals",
    )

    op.drop_table(
        "website_usage_intervals"
    )

    op.drop_index(
        "ix_website_observations_domain_observed_at",
        table_name="website_observations",
    )

    op.drop_index(
        "ix_website_observations_employee_observed_at",
        table_name="website_observations",
    )

    op.drop_index(
        "ix_website_observations_device_observed_at",
        table_name="website_observations",
    )

    op.drop_table(
        "website_observations"
    )