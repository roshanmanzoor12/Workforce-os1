"""add workspace channels

Revision ID: a6b7c8d9e0f1
Revises: f5a6b7c8d9e0
Create Date: 2026-09-08
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "a6b7c8d9e0f1"

down_revision: str | None = (
    "f5a6b7c8d9e0"
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
        "workspace_channels",
        sa.Column(
            "id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),
        sa.Column(
            "workspace_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),
        sa.Column(
            "name",
            sa.String(
                length=120
            ),
            nullable=False,
        ),
        sa.Column(
            "slug",
            sa.String(
                length=120
            ),
            nullable=False,
        ),
        sa.Column(
            "channel_type",
            sa.String(
                length=32
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
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text(
                "true"
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
        sa.ForeignKeyConstraint(
            [
                "workspace_id",
            ],
            [
                "workspaces.id",
            ],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            [
                "created_by_user_id",
            ],
            [
                "users.id",
            ],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "id",
        ),
        sa.UniqueConstraint(
            "workspace_id",
            "slug",
            name=(
                "uq_workspace_channels_"
                "workspace_slug"
            ),
        ),
    )

    op.create_index(
        "ix_workspace_channels_workspace_active",
        "workspace_channels",
        [
            "workspace_id",
            "is_active",
        ],
    )

    op.create_table(
        "workspace_channel_members",
        sa.Column(
            "id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),
        sa.Column(
            "channel_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),
        sa.Column(
            "role",
            sa.String(
                length=32
            ),
            nullable=False,
        ),
        sa.Column(
            "joined_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=False,
            server_default=sa.text(
                "CURRENT_TIMESTAMP"
            ),
        ),
        sa.Column(
            "left_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            [
                "channel_id",
            ],
            [
                "workspace_channels.id",
            ],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            [
                "user_id",
            ],
            [
                "users.id",
            ],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "id",
        ),
        sa.UniqueConstraint(
            "channel_id",
            "user_id",
            name=(
                "uq_workspace_channel_members_"
                "channel_user"
            ),
        ),
    )

    op.create_index(
        "ix_workspace_channel_members_user_active",
        "workspace_channel_members",
        [
            "user_id",
            "left_at",
        ],
    )

    op.create_table(
        "workspace_channel_messages",
        sa.Column(
            "id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),
        sa.Column(
            "channel_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),
        sa.Column(
            "sender_user_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=True,
        ),
        sa.Column(
            "message_type",
            sa.String(
                length=32
            ),
            nullable=False,
        ),
        sa.Column(
            "content",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "edited_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=True,
        ),
        sa.Column(
            "deleted_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=True,
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
            [
                "channel_id",
            ],
            [
                "workspace_channels.id",
            ],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            [
                "sender_user_id",
            ],
            [
                "users.id",
            ],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint(
            "id",
        ),
    )

    op.create_index(
        "ix_workspace_channel_messages_channel_created",
        "workspace_channel_messages",
        [
            "channel_id",
            "created_at",
        ],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_workspace_channel_messages_channel_created",
        table_name=(
            "workspace_channel_messages"
        ),
    )

    op.drop_table(
        "workspace_channel_messages"
    )

    op.drop_index(
        "ix_workspace_channel_members_user_active",
        table_name=(
            "workspace_channel_members"
        ),
    )

    op.drop_table(
        "workspace_channel_members"
    )

    op.drop_index(
        "ix_workspace_channels_workspace_active",
        table_name="workspace_channels",
    )

    op.drop_table(
        "workspace_channels"
    )