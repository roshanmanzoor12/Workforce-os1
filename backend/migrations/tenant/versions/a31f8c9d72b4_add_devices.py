"""add tenant devices

Revision ID: a31f8c9d72b4
Revises: 6da80bf317fd
Create Date: 2026-08-22

Creates the tenant-local device inventory used by WorkforceOS
endpoint registration.

This migration belongs only to tenant databases.

It must never be executed against workforce_control.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# =========================================================
# REVISION IDENTIFIERS
# =========================================================

revision: str = "a31f8c9d72b4"

down_revision: Union[
    str,
    Sequence[str],
    None,
] = "6da80bf317fd"

branch_labels: Union[
    str,
    Sequence[str],
    None,
] = None

depends_on: Union[
    str,
    Sequence[str],
    None,
] = None


# =========================================================
# UPGRADE
# =========================================================


def upgrade() -> None:
    """
    Create tenant-local endpoint device inventory.

    Tenant isolation is provided by the physical tenant database,
    therefore devices intentionally contain no workspace_id or
    database-routing fields.
    """

    op.create_table(
        "devices",

        # -------------------------------------------------
        # DEVICE IDENTITY
        # -------------------------------------------------

        sa.Column(
            "device_uuid",
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

        # -------------------------------------------------
        # MACHINE INFORMATION
        # -------------------------------------------------

        sa.Column(
            "hostname",
            sa.String(
                length=255
            ),
            nullable=False,
        ),

        sa.Column(
            "os_name",
            sa.String(
                length=100
            ),
            nullable=False,
        ),

        sa.Column(
            "os_version",
            sa.String(
                length=100
            ),
            nullable=True,
        ),

        sa.Column(
            "architecture",
            sa.String(
                length=50
            ),
            nullable=True,
        ),

        # -------------------------------------------------
        # AGENT INFORMATION
        # -------------------------------------------------

        sa.Column(
            "agent_version",
            sa.String(
                length=50
            ),
            nullable=True,
        ),

        sa.Column(
            "agent_identifier",
            sa.String(
                length=255
            ),
            nullable=True,
        ),

        # -------------------------------------------------
        # DEVICE LIFECYCLE
        # -------------------------------------------------

        sa.Column(
            "status",
            sa.String(
                length=30
            ),
            nullable=False,
            server_default=sa.text(
                "'pending'"
            ),
        ),

        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text(
                "true"
            ),
        ),

        sa.Column(
            "first_seen_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=True,
        ),

        sa.Column(
            "last_seen_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=True,
        ),

        sa.Column(
            "registered_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=True,
        ),

        sa.Column(
            "revoked_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=True,
        ),

        # -------------------------------------------------
        # FUTURE MONITORING PROFILE
        # -------------------------------------------------

        sa.Column(
            "monitoring_profile_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=True,
        ),

        # -------------------------------------------------
        # STANDARD TENANT MODEL FIELDS
        # -------------------------------------------------

        sa.Column(
            "id",
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
            server_default=sa.text(
                "now()"
            ),
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=False,
            server_default=sa.text(
                "now()"
            ),
        ),

        # -------------------------------------------------
        # FOREIGN KEYS
        # -------------------------------------------------

        sa.ForeignKeyConstraint(
            [
                "employee_id",
            ],
            [
                "employees.id",
            ],
            name=op.f(
                "fk_devices_employee_id_employees"
            ),
            ondelete="SET NULL",
        ),

        # -------------------------------------------------
        # PRIMARY KEY
        # -------------------------------------------------

        sa.PrimaryKeyConstraint(
            "id",
            name=op.f(
                "pk_devices"
            ),
        ),

        # -------------------------------------------------
        # UNIQUE CONSTRAINTS
        # -------------------------------------------------

        sa.UniqueConstraint(
            "device_uuid",
            name="uq_devices_device_uuid",
        ),

        sa.UniqueConstraint(
            "agent_identifier",
            name="uq_devices_agent_identifier",
        ),

        # -------------------------------------------------
        # CHECK CONSTRAINTS
        # -------------------------------------------------

        sa.CheckConstraint(
            (
                "status IN "
                "('pending', 'active', 'offline', "
                "'disabled', 'revoked')"
            ),
            name="ck_devices_status",
        ),
    )

    # =====================================================
    # INDEXES
    # =====================================================

    op.create_index(
        "ix_devices_employee_id",
        "devices",
        [
            "employee_id",
        ],
        unique=False,
    )

    op.create_index(
        "ix_devices_status",
        "devices",
        [
            "status",
        ],
        unique=False,
    )

    op.create_index(
        "ix_devices_is_active",
        "devices",
        [
            "is_active",
        ],
        unique=False,
    )

    op.create_index(
        "ix_devices_last_seen_at",
        "devices",
        [
            "last_seen_at",
        ],
        unique=False,
    )

    op.create_index(
        "ix_devices_hostname",
        "devices",
        [
            "hostname",
        ],
        unique=False,
    )


# =========================================================
# DOWNGRADE
# =========================================================


def downgrade() -> None:
    """
    Remove tenant device inventory.

    This is destructive and removes all registered Device rows.
    """

    op.drop_index(
        "ix_devices_hostname",
        table_name="devices",
    )

    op.drop_index(
        "ix_devices_last_seen_at",
        table_name="devices",
    )

    op.drop_index(
        "ix_devices_is_active",
        table_name="devices",
    )

    op.drop_index(
        "ix_devices_status",
        table_name="devices",
    )

    op.drop_index(
        "ix_devices_employee_id",
        table_name="devices",
    )

    op.drop_table(
        "devices"
    )