from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "h8c9d0e1f2g3"
down_revision = "g7b8c9d0e1f2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "desktop_agent_devices",

        sa.Column(
            "id",
            sa.Uuid(),
            nullable=False,
        ),

        sa.Column(
            "user_id",
            sa.Uuid(),
            nullable=False,
        ),

        sa.Column(
            "employee_id",
            sa.Uuid(),
            nullable=False,
        ),

        sa.Column(
            "installation_id",
            sa.Uuid(),
            nullable=False,
        ),

        sa.Column(
            "device_name",
            sa.String(
                length=255
            ),
            nullable=False,
        ),

        sa.Column(
            "platform",
            sa.String(
                length=32
            ),
            nullable=False,
        ),

        sa.Column(
            "os_version",
            sa.String(
                length=255
            ),
            nullable=True,
        ),

        sa.Column(
            "agent_version",
            sa.String(
                length=100
            ),
            nullable=False,
        ),

        sa.Column(
            "status",
            sa.String(
                length=32
            ),
            nullable=False,
            server_default=(
                "online"
            ),
        ),

        sa.Column(
            "is_disabled",
            sa.Boolean(),
            nullable=False,
            server_default=(
                sa.text(
                    "false"
                )
            ),
        ),

        sa.Column(
            "consent_version",
            sa.String(
                length=100
            ),
            nullable=False,
        ),

        sa.Column(
            "consent_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=False,
        ),

        sa.Column(
            "capabilities",
            postgresql.JSONB(
                astext_type=sa.Text()
            ),
            nullable=False,
            server_default=(
                sa.text(
                    "'{}'::jsonb"
                )
            ),
        ),

        sa.Column(
            "last_seen_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=False,
            server_default=(
                sa.text(
                    "now()"
                )
            ),
        ),

        sa.Column(
            "last_ip_address",
            sa.String(
                length=64
            ),
            nullable=True,
        ),

        sa.Column(
            "registered_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=False,
            server_default=(
                sa.text(
                    "now()"
                )
            ),
        ),

        sa.Column(
            "created_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=False,
            server_default=(
                sa.text(
                    "now()"
                )
            ),
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=False,
            server_default=(
                sa.text(
                    "now()"
                )
            ),
        ),

        sa.PrimaryKeyConstraint(
            "id",
        ),

        sa.UniqueConstraint(
            "installation_id",
            name=(
                "uq_desktop_agent_devices_"
                "installation_id"
            ),
        ),
    )

    op.create_index(
        "ix_desktop_agent_devices_user",
        "desktop_agent_devices",
        [
            "user_id",
        ],
        unique=False,
    )

    op.create_index(
        "ix_desktop_agent_devices_employee",
        "desktop_agent_devices",
        [
            "employee_id",
        ],
        unique=False,
    )

    op.create_index(
        "ix_desktop_agent_devices_status_seen",
        "desktop_agent_devices",
        [
            "status",
            "last_seen_at",
        ],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_desktop_agent_devices_status_seen",
        table_name=(
            "desktop_agent_devices"
        ),
    )

    op.drop_index(
        "ix_desktop_agent_devices_employee",
        table_name=(
            "desktop_agent_devices"
        ),
    )

    op.drop_index(
        "ix_desktop_agent_devices_user",
        table_name=(
            "desktop_agent_devices"
        ),
    )

    op.drop_table(
        "desktop_agent_devices"
    )