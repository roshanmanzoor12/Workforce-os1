from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# =========================================================
# ALEMBIC REVISION
# =========================================================

revision: str = "d82af39c61e7"
down_revision: str | None = "b7419de52ac8"

branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# =========================================================
# UPGRADE
# =========================================================


def upgrade() -> None:
    """
    Add the control-plane device_routes table.

    DeviceRoute allows the backend to resolve:

        device_uuid
            ↓
        workspace_id
            ↓
        trusted TenantDatabaseRegistry
            ↓
        physical tenant database
            ↓
        tenant-local Device

    No physical tenant database identifier is accepted from
    endpoint agents.
    """

    op.create_table(
        "device_routes",

        # -------------------------------------------------
        # STANDARD MODEL FIELDS
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
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=False,
        ),

        # -------------------------------------------------
        # WORKSPACE
        # -------------------------------------------------

        sa.Column(
            "workspace_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),

        # -------------------------------------------------
        # GLOBAL DEVICE IDENTITY
        # -------------------------------------------------

        sa.Column(
            "device_uuid",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),

        # -------------------------------------------------
        # TENANT-LOCAL DEVICE IDENTITY
        # -------------------------------------------------

        sa.Column(
            "tenant_device_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),

        # -------------------------------------------------
        # LIFECYCLE
        # -------------------------------------------------

        sa.Column(
            "status",
            sa.String(
                length=50
            ),
            nullable=False,
        ),

        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
        ),

        sa.Column(
            "registered_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=False,
        ),

        sa.Column(
            "revoked_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=True,
        ),

        # -------------------------------------------------
        # PRIMARY KEY
        # -------------------------------------------------

        sa.PrimaryKeyConstraint(
            "id",
            name="pk_device_routes",
        ),

        # -------------------------------------------------
        # FOREIGN KEYS
        # -------------------------------------------------

        sa.ForeignKeyConstraint(
            [
                "workspace_id",
            ],
            [
                "workspaces.id",
            ],
            name=(
                "fk_device_routes_workspace_id_"
                "workspaces"
            ),
            ondelete="CASCADE",
        ),

        # -------------------------------------------------
        # UNIQUE CONSTRAINTS
        # -------------------------------------------------

        sa.UniqueConstraint(
            "device_uuid",
            name="uq_device_routes_device_uuid",
        ),

        sa.UniqueConstraint(
            "workspace_id",
            "tenant_device_id",
            name=(
                "uq_device_routes_workspace_"
                "tenant_device"
            ),
        ),

        # -------------------------------------------------
        # CHECK CONSTRAINTS
        # -------------------------------------------------

        sa.CheckConstraint(
            "status IN ('active', 'revoked')",
            name="ck_device_routes_status",
        ),
    )

    # =====================================================
    # INDEXES
    # =====================================================

    op.create_index(
        "ix_device_routes_workspace_id",
        "device_routes",
        [
            "workspace_id",
        ],
        unique=False,
    )

    op.create_index(
        "ix_device_routes_status",
        "device_routes",
        [
            "status",
        ],
        unique=False,
    )

    op.create_index(
        "ix_device_routes_is_active",
        "device_routes",
        [
            "is_active",
        ],
        unique=False,
    )


# =========================================================
# DOWNGRADE
# =========================================================


def downgrade() -> None:
    """
    Remove control-plane device routing.
    """

    op.drop_index(
        "ix_device_routes_is_active",
        table_name="device_routes",
    )

    op.drop_index(
        "ix_device_routes_status",
        table_name="device_routes",
    )

    op.drop_index(
        "ix_device_routes_workspace_id",
        table_name="device_routes",
    )

    op.drop_table(
        "device_routes"
    )


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "revision",
    "down_revision",
    "branch_labels",
    "depends_on",
    "upgrade",
    "downgrade",
]