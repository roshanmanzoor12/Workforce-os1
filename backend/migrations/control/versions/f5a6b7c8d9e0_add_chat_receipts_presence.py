"""add chat receipts and presence

Revision ID: f5a6b7c8d9e0
Revises: e4f5a6b7c8d9
Create Date: 2026-09-08
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "f5a6b7c8d9e0"

down_revision: str | None = (
    "e4f5a6b7c8d9"
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
        "chat_message_receipts",
        sa.Column(
            "id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),
        sa.Column(
            "message_id",
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
            "read_at",
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
                "message_id",
            ],
            [
                "chat_messages.id",
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
            "message_id",
            "user_id",
            name=(
                "uq_chat_message_receipts_"
                "message_user"
            ),
        ),
    )

    op.create_index(
        "ix_chat_message_receipts_user_read",
        "chat_message_receipts",
        [
            "user_id",
            "read_at",
        ],
    )

    op.create_table(
        "chat_presence",
        sa.Column(
            "user_id",
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
            server_default="offline",
        ),
        sa.Column(
            "last_seen_at",
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
                "user_id",
            ],
            [
                "users.id",
            ],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "user_id",
        ),
    )


def downgrade() -> None:
    op.drop_table(
        "chat_presence"
    )

    op.drop_index(
        "ix_chat_message_receipts_user_read",
        table_name="chat_message_receipts",
    )

    op.drop_table(
        "chat_message_receipts"
    )