"""add device routes

Revision ID: d82af39c61e7
Revises: b7419de52ac8
Create Date: 2026-08-22

Creates control-plane routing identities for registered endpoint
devices.

device_routes allows the backend to resolve:

    device_uuid
        -> workspace_id
        -> trusted TenantDatabaseRegistry
        -> correct tenant database

without allowing the endpoint agent to choose database routing
information and without scanning tenant databases.

This migration belongs only to workforce_control.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# =========================================================
# REVISION IDENTIFIERS
# =========================================================

revision: str = "d82af39c61e7"

down_revision: Union[
    str,
    Sequence[str],
    None,
] = "b7419de52ac8"

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
    Create control-plane device routing identities.

    tenant_device_id intentionally has no foreign key because
    the Device row exists in a separate physical tenant database.
    """

    op.create_table(
        "device_routes",

        # -------------------------------------------------
        # WORKSPACE BINDING
        # -------------------------------------------------

        sa.Column(
            "workspace_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),

        # -------------------------------------------------
        # GLOBAL DEVICE ROUTING IDENTITY
        # -------------------------------------------------

        sa.Column(
            "device_uuid",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),

        # -------------------------------------------------
        # TENANT DEVICE IDENTITY
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
                length=30
            ),
            nullable=False,
            server_default=sa.text(
                "'active'"
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
        # STANDARD CONTROL MODEL FIELDS
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
        # FOREIGN KEY
        # -------------------------------------------------

        sa.ForeignKeyConstraint(
            [
                "workspace_id",
            ],
            [
                "workspaces.id",
            ],
            name=op.f(
                "fk_device_routes_workspace_id_workspaces"
            ),
            ondelete="CASCADE",
        ),

        # -------------------------------------------------
        # PRIMARY KEY
        # -------------------------------------------------

        sa.PrimaryKeyConstraint(
            "id",
            name=op.f(
                "pk_device_routes"
            ),
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
                "uq_device_routes_"
                "workspace_id_tenant_device_id"
            ),
        ),

        # -------------------------------------------------
        # CHECK CONSTRAINTS
        # -------------------------------------------------

        sa.CheckConstraint(
            (
                "status IN "
                "('active', 'revoked')"
            ),
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
    Remove control-plane device routing identities.
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