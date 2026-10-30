"""add device activation codes

Revision ID: b7419de52ac8
Revises: ad1feae99c4b
Create Date: 2026-08-22

Creates control-plane device activation codes used to bootstrap
trusted endpoint enrollment.

This migration belongs only to the WorkforceOS control database.

Plaintext activation codes are never persisted.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# =========================================================
# REVISION IDENTIFIERS
# =========================================================

revision: str = "b7419de52ac8"

down_revision: Union[
    str,
    Sequence[str],
    None,
] = "ad1feae99c4b"

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
    Create control-plane activation-code storage.

    The activation code resolves one trusted workspace before
    any tenant database is opened.
    """

    op.create_table(
        "device_activation_codes",

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

        sa.Column(
            "created_by_user_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),

        # -------------------------------------------------
        # SECRET MATERIAL
        # -------------------------------------------------

        sa.Column(
            "code_hash",
            sa.String(
                length=255
            ),
            nullable=False,
        ),

        sa.Column(
            "code_prefix",
            sa.String(
                length=32
            ),
            nullable=True,
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
            "expires_at",
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

        sa.Column(
            "last_used_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=True,
        ),

        # -------------------------------------------------
        # USAGE LIMITS
        # -------------------------------------------------

        sa.Column(
            "max_uses",
            sa.Integer(),
            nullable=True,
        ),

        sa.Column(
            "used_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text(
                "0"
            ),
        ),

        # -------------------------------------------------
        # ADMIN LABEL
        # -------------------------------------------------

        sa.Column(
            "label",
            sa.String(
                length=150
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
        # FOREIGN KEYS
        # -------------------------------------------------

        sa.ForeignKeyConstraint(
            [
                "workspace_id",
            ],
            [
                "workspaces.id",
            ],
            name=op.f(
                "fk_device_activation_codes_workspace_id_workspaces"
            ),
            ondelete="CASCADE",
        ),

        sa.ForeignKeyConstraint(
            [
                "created_by_user_id",
            ],
            [
                "users.id",
            ],
            name=op.f(
                "fk_device_activation_codes_created_by_user_id_users"
            ),
            ondelete="CASCADE",
        ),

        # -------------------------------------------------
        # PRIMARY KEY
        # -------------------------------------------------

        sa.PrimaryKeyConstraint(
            "id",
            name=op.f(
                "pk_device_activation_codes"
            ),
        ),

        # -------------------------------------------------
        # UNIQUE CONSTRAINTS
        # -------------------------------------------------

        sa.UniqueConstraint(
            "code_hash",
            name="uq_device_activation_codes_code_hash",
        ),

        # -------------------------------------------------
        # CHECK CONSTRAINTS
        # -------------------------------------------------

        sa.CheckConstraint(
            (
                "status IN "
                "('active', 'expired', "
                "'revoked', 'exhausted')"
            ),
            name="ck_device_activation_codes_status",
        ),

        sa.CheckConstraint(
            (
                "max_uses IS NULL "
                "OR max_uses > 0"
            ),
            name=(
                "ck_device_activation_codes_"
                "max_uses_positive"
            ),
        ),

        sa.CheckConstraint(
            "used_count >= 0",
            name=(
                "ck_device_activation_codes_"
                "used_count_nonnegative"
            ),
        ),
    )

    # =====================================================
    # INDEXES
    # =====================================================

    op.create_index(
        "ix_device_activation_codes_workspace_id",
        "device_activation_codes",
        [
            "workspace_id",
        ],
        unique=False,
    )

    op.create_index(
        "ix_device_activation_codes_status",
        "device_activation_codes",
        [
            "status",
        ],
        unique=False,
    )

    op.create_index(
        "ix_device_activation_codes_expires_at",
        "device_activation_codes",
        [
            "expires_at",
        ],
        unique=False,
    )

    op.create_index(
        "ix_device_activation_codes_is_active",
        "device_activation_codes",
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
    Remove control-plane device activation-code storage.
    """

    op.drop_index(
        "ix_device_activation_codes_is_active",
        table_name="device_activation_codes",
    )

    op.drop_index(
        "ix_device_activation_codes_expires_at",
        table_name="device_activation_codes",
    )

    op.drop_index(
        "ix_device_activation_codes_status",
        table_name="device_activation_codes",
    )

    op.drop_index(
        "ix_device_activation_codes_workspace_id",
        table_name="device_activation_codes",
    )

    op.drop_table(
        "device_activation_codes"
    )