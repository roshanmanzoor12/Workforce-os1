"""add device credentials

Revision ID: c5e4d7a91b26
Revises: a31f8c9d72b4
Create Date: 2026-08-22

Creates tenant-local device credentials used by registered
WorkforceOS agents for ongoing authenticated communication.

Plaintext device secrets are never persisted.

This migration belongs only to tenant databases.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# =========================================================
# REVISION IDENTIFIERS
# =========================================================

revision: str = "c5e4d7a91b26"

down_revision: Union[
    str,
    Sequence[str],
    None,
] = "a31f8c9d72b4"

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
    Create tenant-local authentication credentials for devices.

    Credentials are bound to tenant-local Device rows.

    Only secret hashes are stored. Plaintext device secrets are
    returned to an agent only when initially issued or rotated.
    """

    op.create_table(
        "device_credentials",

        # -------------------------------------------------
        # DEVICE BINDING
        # -------------------------------------------------

        sa.Column(
            "device_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),

        # -------------------------------------------------
        # SECRET MATERIAL
        # -------------------------------------------------

        sa.Column(
            "secret_hash",
            sa.String(
                length=255
            ),
            nullable=False,
        ),

        sa.Column(
            "secret_prefix",
            sa.String(
                length=32
            ),
            nullable=True,
        ),

        # -------------------------------------------------
        # CREDENTIAL VERSION
        # -------------------------------------------------

        sa.Column(
            "version",
            sa.Integer(),
            nullable=False,
            server_default=sa.text(
                "1"
            ),
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
            "issued_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=True,
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
        # FOREIGN KEY
        # -------------------------------------------------

        sa.ForeignKeyConstraint(
            [
                "device_id",
            ],
            [
                "devices.id",
            ],
            name=op.f(
                "fk_device_credentials_device_id_devices"
            ),
            ondelete="CASCADE",
        ),

        # -------------------------------------------------
        # PRIMARY KEY
        # -------------------------------------------------

        sa.PrimaryKeyConstraint(
            "id",
            name=op.f(
                "pk_device_credentials"
            ),
        ),

        # -------------------------------------------------
        # UNIQUE CONSTRAINTS
        # -------------------------------------------------

        sa.UniqueConstraint(
            "secret_hash",
            name="uq_device_credentials_secret_hash",
        ),

        sa.UniqueConstraint(
            "device_id",
            "version",
            name="uq_device_credentials_device_id_version",
        ),

        # -------------------------------------------------
        # CHECK CONSTRAINTS
        # -------------------------------------------------

        sa.CheckConstraint(
            (
                "status IN "
                "('active', 'revoked', 'expired')"
            ),
            name="ck_device_credentials_status",
        ),

        sa.CheckConstraint(
            "version > 0",
            name="ck_device_credentials_version_positive",
        ),
    )

    # =====================================================
    # INDEXES
    # =====================================================

    op.create_index(
        "ix_device_credentials_device_id",
        "device_credentials",
        [
            "device_id",
        ],
        unique=False,
    )

    op.create_index(
        "ix_device_credentials_status",
        "device_credentials",
        [
            "status",
        ],
        unique=False,
    )

    op.create_index(
        "ix_device_credentials_is_active",
        "device_credentials",
        [
            "is_active",
        ],
        unique=False,
    )

    op.create_index(
        "ix_device_credentials_expires_at",
        "device_credentials",
        [
            "expires_at",
        ],
        unique=False,
    )

    op.create_index(
        "ix_device_credentials_last_used_at",
        "device_credentials",
        [
            "last_used_at",
        ],
        unique=False,
    )


# =========================================================
# DOWNGRADE
# =========================================================


def downgrade() -> None:
    """
    Remove tenant-local device credential storage.

    This is destructive and invalidates stored device
    authentication credentials.
    """

    op.drop_index(
        "ix_device_credentials_last_used_at",
        table_name="device_credentials",
    )

    op.drop_index(
        "ix_device_credentials_expires_at",
        table_name="device_credentials",
    )

    op.drop_index(
        "ix_device_credentials_is_active",
        table_name="device_credentials",
    )

    op.drop_index(
        "ix_device_credentials_status",
        table_name="device_credentials",
    )

    op.drop_index(
        "ix_device_credentials_device_id",
        table_name="device_credentials",
    )

    op.drop_table(
        "device_credentials"
    )