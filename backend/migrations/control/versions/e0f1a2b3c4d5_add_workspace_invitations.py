"""add workspace invitations

Revision ID: e0f1a2b3c4d5
Revises: d9e0f1a2b3c4
Create Date: 2026-09-21
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "e0f1a2b3c4d5"

down_revision: str | None = (
    "d9e0f1a2b3c4"
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
    op.create_table(
        "workspace_invitations",

        sa.Column(
            "workspace_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),

        # Tenant-local logical references.
        # No control-plane FK.
        sa.Column(
            "employee_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=True,
        ),

        sa.Column(
            "email",
            sa.String(
                length=320
            ),
            nullable=False,
        ),

        sa.Column(
            "invited_user_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=True,
        ),

        sa.Column(
            "role_key",
            sa.String(
                length=64
            ),
            nullable=False,
            server_default=sa.text(
                "'member'"
            ),
        ),

        # Tenant-local logical reference.
        sa.Column(
            "department_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=True,
        ),

        # Tenant-local logical reference.
        sa.Column(
            "team_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=True,
        ),

        sa.Column(
            "manager_membership_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=True,
        ),

        sa.Column(
            "invited_by_user_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),

        # Raw token is never persisted.
        sa.Column(
            "token_hash",
            sa.String(
                length=64
            ),
            nullable=False,
        ),

        sa.Column(
            "status",
            sa.String(
                length=32
            ),
            nullable=False,
            server_default=sa.text(
                "'pending'"
            ),
        ),

        sa.Column(
            "expires_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=False,
        ),

        sa.Column(
            "accepted_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=True,
        ),

        sa.Column(
            "declined_at",
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
            name="fk_wsi_workspace",
        ),

        sa.ForeignKeyConstraint(
            ["invited_user_id"],
            ["users.id"],
            ondelete="SET NULL",
            name="fk_wsi_invited_user",
        ),

        sa.ForeignKeyConstraint(
            ["manager_membership_id"],
            ["workspace_memberships.id"],
            ondelete="SET NULL",
            name="fk_wsi_manager_member",
        ),

        sa.ForeignKeyConstraint(
            ["invited_by_user_id"],
            ["users.id"],
            ondelete="RESTRICT",
            name="fk_wsi_invited_by",
        ),

        sa.PrimaryKeyConstraint(
            "id",
            name="pk_workspace_invitations",
        ),

        sa.UniqueConstraint(
            "token_hash",
            name="uq_wsi_token_hash",
        ),

        sa.CheckConstraint(
            (
                "status IN "
                "('pending', "
                "'accepted', "
                "'declined', "
                "'expired', "
                "'revoked')"
            ),
            name="ck_wsi_status",
        ),
    )

    op.create_index(
        "ix_wsi_workspace_status",
        "workspace_invitations",
        [
            "workspace_id",
            "status",
        ],
        unique=False,
    )

    op.create_index(
        "ix_wsi_workspace_email",
        "workspace_invitations",
        [
            "workspace_id",
            "email",
        ],
        unique=False,
    )

    op.create_index(
        "ix_wsi_expires_at",
        "workspace_invitations",
        [
            "expires_at",
        ],
        unique=False,
    )

    op.create_index(
        "ix_wsi_created_at",
        "workspace_invitations",
        [
            "created_at",
        ],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_wsi_created_at",
        table_name="workspace_invitations",
    )

    op.drop_index(
        "ix_wsi_expires_at",
        table_name="workspace_invitations",
    )

    op.drop_index(
        "ix_wsi_workspace_email",
        table_name="workspace_invitations",
    )

    op.drop_index(
        "ix_wsi_workspace_status",
        table_name="workspace_invitations",
    )

    op.drop_table(
        "workspace_invitations"
    )