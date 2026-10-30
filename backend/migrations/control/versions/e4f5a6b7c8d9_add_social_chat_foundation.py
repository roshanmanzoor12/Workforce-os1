"""add social chat foundation

Revision ID: e4f5a6b7c8d9
Revises: d3e4f5a6b7c8
Create Date: 2026-09-03
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "e4f5a6b7c8d9"

down_revision: str | None = (
    "d3e4f5a6b7c8"
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
        "friendships",
        sa.Column(
            "id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),
        sa.Column(
            "user_low_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),
        sa.Column(
            "user_high_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),
        sa.Column(
            "requested_by_user_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(
                length=32
            ),
            nullable=False,
            server_default="pending",
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
        sa.Column(
            "accepted_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=True,
        ),
        sa.Column(
            "blocked_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=True,
        ),
        sa.CheckConstraint(
            "user_low_id <> user_high_id",
            name="ck_friendships_distinct_users",
        ),
        sa.ForeignKeyConstraint(
            [
                "user_low_id",
            ],
            [
                "users.id",
            ],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            [
                "user_high_id",
            ],
            [
                "users.id",
            ],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            [
                "requested_by_user_id",
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
            "user_low_id",
            "user_high_id",
            name="uq_friendships_user_pair",
        ),
    )

    op.create_index(
        "ix_friendships_user_low_status",
        "friendships",
        [
            "user_low_id",
            "status",
        ],
    )

    op.create_index(
        "ix_friendships_user_high_status",
        "friendships",
        [
            "user_high_id",
            "status",
        ],
    )

    op.create_table(
        "conversations",
        sa.Column(
            "id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),
        sa.Column(
            "conversation_type",
            sa.String(
                length=32
            ),
            nullable=False,
        ),
        sa.Column(
            "name",
            sa.String(
                length=120
            ),
            nullable=True,
        ),
        sa.Column(
            "created_by_user_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),
        sa.Column(
            "direct_user_low_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=True,
        ),
        sa.Column(
            "direct_user_high_id",
            postgresql.UUID(
                as_uuid=True
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
        sa.CheckConstraint(
            """
            (
                conversation_type = 'direct'
                AND direct_user_low_id IS NOT NULL
                AND direct_user_high_id IS NOT NULL
                AND direct_user_low_id <> direct_user_high_id
            )
            OR
            (
                conversation_type = 'group'
                AND direct_user_low_id IS NULL
                AND direct_user_high_id IS NULL
            )
            """,
            name="ck_conversations_type_shape",
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
        sa.ForeignKeyConstraint(
            [
                "direct_user_low_id",
            ],
            [
                "users.id",
            ],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            [
                "direct_user_high_id",
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
            "direct_user_low_id",
            "direct_user_high_id",
            name="uq_conversations_direct_pair",
        ),
    )

    op.create_index(
        "ix_conversations_updated_at",
        "conversations",
        [
            "updated_at",
        ],
    )

    op.create_table(
        "conversation_members",
        sa.Column(
            "id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),
        sa.Column(
            "conversation_id",
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
            server_default="member",
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
                "conversation_id",
            ],
            [
                "conversations.id",
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
            "conversation_id",
            "user_id",
            name="uq_conversation_members_user",
        ),
    )

    op.create_index(
        "ix_conversation_members_user_id",
        "conversation_members",
        [
            "user_id",
        ],
    )

    op.create_table(
        "chat_messages",
        sa.Column(
            "id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),
        sa.Column(
            "conversation_id",
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
            server_default="text",
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
                "conversation_id",
            ],
            [
                "conversations.id",
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
        "ix_chat_messages_conversation_created",
        "chat_messages",
        [
            "conversation_id",
            "created_at",
        ],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_chat_messages_conversation_created",
        table_name="chat_messages",
    )

    op.drop_table(
        "chat_messages"
    )

    op.drop_index(
        "ix_conversation_members_user_id",
        table_name="conversation_members",
    )

    op.drop_table(
        "conversation_members"
    )

    op.drop_index(
        "ix_conversations_updated_at",
        table_name="conversations",
    )

    op.drop_table(
        "conversations"
    )

    op.drop_index(
        "ix_friendships_user_high_status",
        table_name="friendships",
    )

    op.drop_index(
        "ix_friendships_user_low_status",
        table_name="friendships",
    )

    op.drop_table(
        "friendships"
    )