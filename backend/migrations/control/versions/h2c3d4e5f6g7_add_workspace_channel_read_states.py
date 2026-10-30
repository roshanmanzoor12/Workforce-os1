from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import (
    postgresql,
)


revision = "h2c3d4e5f6g7"

down_revision = "g1b2c3d4e5f6"

branch_labels = None

depends_on = None


def upgrade() -> None:
    op.create_table(
        "workspace_channel_read_states",

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
            "last_read_message_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=True,
        ),

        sa.Column(
            "last_read_at",
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

        sa.ForeignKeyConstraint(
            [
                "last_read_message_id",
            ],
            [
                "workspace_channel_messages.id",
            ],
            ondelete="SET NULL",
        ),

        sa.PrimaryKeyConstraint(
            "id"
        ),

        sa.UniqueConstraint(
            "channel_id",
            "user_id",
            name=(
                "uq_workspace_channel_"
                "read_states_channel_user"
            ),
        ),
    )

    op.create_index(
        "ix_workspace_channel_"
        "read_states_user",
        "workspace_channel_read_states",
        [
            "user_id",
        ],
        unique=False,
    )

    op.create_index(
        "ix_workspace_channel_"
        "read_states_channel",
        "workspace_channel_read_states",
        [
            "channel_id",
        ],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_workspace_channel_"
        "read_states_channel",
        table_name=(
            "workspace_channel_read_states"
        ),
    )

    op.drop_index(
        "ix_workspace_channel_"
        "read_states_user",
        table_name=(
            "workspace_channel_read_states"
        ),
    )

    op.drop_table(
        "workspace_channel_read_states"
    )