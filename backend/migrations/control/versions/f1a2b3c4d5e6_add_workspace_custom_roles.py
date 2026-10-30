"""add workspace custom roles and membership moderation

Revision ID: f1a2b3c4d5e6
Revises: e0f1a2b3c4d5
Create Date: 2026-09-21
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "f1a2b3c4d5e6"

down_revision: str | None = (
    "e0f1a2b3c4d5"
)

branch_labels: (
    str
    | Sequence[str]
    | None
) = None

depends_on: (
    str
    | Sequence[str]
    | None
) = None


def upgrade() -> None:
    # =====================================================
    # CUSTOM ROLES
    # =====================================================

    op.create_table(
        "workspace_custom_roles",

        sa.Column(
            "workspace_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),

        sa.Column(
            "role_key",
            sa.String(
                length=64
            ),
            nullable=False,
        ),

        sa.Column(
            "display_name",
            sa.String(
                length=120
            ),
            nullable=False,
        ),

        sa.Column(
            "description",
            sa.String(
                length=500
            ),
            nullable=True,
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
            "created_by_user_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),

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

        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            ondelete="CASCADE",
            name="fk_wcr_workspace",
        ),

        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            ondelete="RESTRICT",
            name="fk_wcr_created_by",
        ),

        sa.PrimaryKeyConstraint(
            "id",
            name="pk_workspace_custom_roles",
        ),

        sa.UniqueConstraint(
            "workspace_id",
            "role_key",
            name="uq_wcr_workspace_role_key",
        ),
    )

    op.create_index(
        "ix_wcr_workspace_id",
        "workspace_custom_roles",
        ["workspace_id"],
        unique=False,
    )

    # =====================================================
    # CUSTOM ROLE PERMISSIONS
    # =====================================================

    op.create_table(
        "workspace_custom_role_permissions",

        sa.Column(
            "role_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),

        sa.Column(
            "permission_key",
            sa.String(
                length=150
            ),
            nullable=False,
        ),

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

        sa.ForeignKeyConstraint(
            ["role_id"],
            ["workspace_custom_roles.id"],
            ondelete="CASCADE",
            name="fk_wcrp_role",
        ),

        sa.PrimaryKeyConstraint(
            "id",
            name="pk_workspace_custom_role_permissions",
        ),

        sa.UniqueConstraint(
            "role_id",
            "permission_key",
            name="uq_wcrp_role_permission",
        ),
    )

    op.create_index(
        "ix_wcrp_role_id",
        "workspace_custom_role_permissions",
        ["role_id"],
        unique=False,
    )

    # =====================================================
    # MEMBERSHIP MODERATION
    # =====================================================

    op.create_table(
        "workspace_membership_moderation",

        sa.Column(
            "membership_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),

        sa.Column(
            "is_banned",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text(
                "false"
            ),
        ),

        sa.Column(
            "is_muted",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text(
                "false"
            ),
        ),

        sa.Column(
            "is_deafened",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text(
                "false"
            ),
        ),

        sa.Column(
            "is_hidden",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text(
                "false"
            ),
        ),

        sa.Column(
            "banned_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=True,
        ),

        sa.Column(
            "banned_by_user_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=True,
        ),

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

        sa.ForeignKeyConstraint(
            ["membership_id"],
            ["workspace_memberships.id"],
            ondelete="CASCADE",
            name="fk_wmm_membership",
        ),

        sa.ForeignKeyConstraint(
            ["banned_by_user_id"],
            ["users.id"],
            ondelete="SET NULL",
            name="fk_wmm_banned_by",
        ),

        sa.PrimaryKeyConstraint(
            "id",
            name="pk_workspace_membership_moderation",
        ),

        sa.UniqueConstraint(
            "membership_id",
            name="uq_wmm_membership",
        ),
    )


def downgrade() -> None:
    op.drop_table(
        "workspace_membership_moderation"
    )

    op.drop_index(
        "ix_wcrp_role_id",
        table_name=(
            "workspace_custom_role_permissions"
        ),
    )

    op.drop_table(
        "workspace_custom_role_permissions"
    )

    op.drop_index(
        "ix_wcr_workspace_id",
        table_name=(
            "workspace_custom_roles"
        ),
    )

    op.drop_table(
        "workspace_custom_roles"
    )