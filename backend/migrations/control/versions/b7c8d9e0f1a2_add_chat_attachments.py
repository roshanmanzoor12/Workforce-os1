"""add chat attachments

Revision ID: b7c8d9e0f1a2
Revises: a6b7c8d9e0f1
Create Date: 2026-09-08

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "b7c8d9e0f1a2"

down_revision: Union[str, None] = (
    "a6b7c8d9e0f1"
)

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


attachment_scope_enum = postgresql.ENUM(
    "CONVERSATION",
    "CHANNEL",
    name="attachment_scope",
    create_type=False,
)

attachment_status_enum = postgresql.ENUM(
    "PENDING",
    "READY",
    "DELETED",
    "FAILED",
    name="attachment_status",
    create_type=False,
)

attachment_kind_enum = postgresql.ENUM(
    "IMAGE",
    "VIDEO",
    "AUDIO",
    "FILE",
    name="attachment_kind",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()

    # -----------------------------------------------------
    # PostgreSQL enum types
    #
    # create_type=False prevents op.create_table() from
    # attempting to CREATE TYPE a second time.
    # -----------------------------------------------------

    attachment_scope_enum.create(
        bind,
        checkfirst=True,
    )

    attachment_status_enum.create(
        bind,
        checkfirst=True,
    )

    attachment_kind_enum.create(
        bind,
        checkfirst=True,
    )

    # -----------------------------------------------------
    # Attachments
    # -----------------------------------------------------

    op.create_table(
        "attachments",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "owner_user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "scope",
            attachment_scope_enum,
            nullable=False,
        ),
        sa.Column(
            "conversation_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "channel_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "message_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "kind",
            attachment_kind_enum,
            nullable=False,
        ),
        sa.Column(
            "status",
            attachment_status_enum,
            nullable=False,
        ),
        sa.Column(
            "original_filename",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "content_type",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "size_bytes",
            sa.BigInteger(),
            nullable=False,
        ),
        sa.Column(
            "bucket_name",
            sa.String(length=128),
            nullable=False,
        ),
        sa.Column(
            "object_key",
            sa.String(length=1024),
            nullable=False,
        ),
        sa.Column(
            "checksum_sha256",
            sa.String(length=64),
            nullable=True,
        ),
        sa.Column(
            "failure_reason",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "ready_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "deleted_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint(
            "id",
        ),
        sa.UniqueConstraint(
            "object_key",
            name="uq_attachments_object_key",
        ),
        sa.CheckConstraint(
            "("
            "scope = 'CONVERSATION' "
            "AND conversation_id IS NOT NULL "
            "AND channel_id IS NULL"
            ") OR ("
            "scope = 'CHANNEL' "
            "AND channel_id IS NOT NULL "
            "AND conversation_id IS NULL"
            ")",
            name="ck_attachment_scope_target",
        ),
        sa.CheckConstraint(
            "size_bytes > 0",
            name="ck_attachment_positive_size",
        ),
    )

    # -----------------------------------------------------
    # Indexes
    # -----------------------------------------------------

    op.create_index(
        "ix_attachments_owner_user_id",
        "attachments",
        ["owner_user_id"],
        unique=False,
    )

    op.create_index(
        "ix_attachments_conversation_id",
        "attachments",
        ["conversation_id"],
        unique=False,
    )

    op.create_index(
        "ix_attachments_channel_id",
        "attachments",
        ["channel_id"],
        unique=False,
    )

    op.create_index(
        "ix_attachments_message_id",
        "attachments",
        ["message_id"],
        unique=False,
    )

    op.create_index(
        "ix_attachments_status",
        "attachments",
        ["status"],
        unique=False,
    )

    op.create_index(
        "ix_attachments_conversation_created",
        "attachments",
        [
            "conversation_id",
            "created_at",
        ],
        unique=False,
    )

    op.create_index(
        "ix_attachments_channel_created",
        "attachments",
        [
            "channel_id",
            "created_at",
        ],
        unique=False,
    )

    op.create_index(
        "ix_attachments_owner_created",
        "attachments",
        [
            "owner_user_id",
            "created_at",
        ],
        unique=False,
    )


def downgrade() -> None:
    # -----------------------------------------------------
    # Indexes
    # -----------------------------------------------------

    op.drop_index(
        "ix_attachments_owner_created",
        table_name="attachments",
    )

    op.drop_index(
        "ix_attachments_channel_created",
        table_name="attachments",
    )

    op.drop_index(
        "ix_attachments_conversation_created",
        table_name="attachments",
    )

    op.drop_index(
        "ix_attachments_status",
        table_name="attachments",
    )

    op.drop_index(
        "ix_attachments_message_id",
        table_name="attachments",
    )

    op.drop_index(
        "ix_attachments_channel_id",
        table_name="attachments",
    )

    op.drop_index(
        "ix_attachments_conversation_id",
        table_name="attachments",
    )

    op.drop_index(
        "ix_attachments_owner_user_id",
        table_name="attachments",
    )

    # -----------------------------------------------------
    # Table
    # -----------------------------------------------------

    op.drop_table(
        "attachments"
    )

    # -----------------------------------------------------
    # PostgreSQL enum types
    # -----------------------------------------------------

    bind = op.get_bind()

    attachment_kind_enum.drop(
        bind,
        checkfirst=True,
    )

    attachment_status_enum.drop(
        bind,
        checkfirst=True,
    )

    attachment_scope_enum.drop(
        bind,
        checkfirst=True,
    )