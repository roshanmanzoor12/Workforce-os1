"""add realtime calls

Revision ID: c8d9e0f1a2b3
Revises: b7c8d9e0f1a2
Create Date: 2026-09-09

"""

from typing import (
    Sequence,
    Union,
)

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import (
    postgresql,
)


revision: str = "c8d9e0f1a2b3"

down_revision: Union[
    str,
    None,
] = "b7c8d9e0f1a2"

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


call_scope_enum = postgresql.ENUM(
    "CONVERSATION",
    "CHANNEL",
    name="call_scope",
    create_type=False,
)

call_kind_enum = postgresql.ENUM(
    "VOICE",
    "VIDEO",
    name="call_kind",
    create_type=False,
)

call_status_enum = postgresql.ENUM(
    "RINGING",
    "ACTIVE",
    "ENDED",
    "CANCELLED",
    name="call_status",
    create_type=False,
)

participant_state_enum = (
    postgresql.ENUM(
        "INVITED",
        "JOINED",
        "LEFT",
        "DECLINED",
        name="call_participant_state",
        create_type=False,
    )
)

screen_share_state_enum = (
    postgresql.ENUM(
        "STOPPED",
        "ACTIVE",
        name="screen_share_state",
        create_type=False,
    )
)


def upgrade() -> None:
    bind = op.get_bind()

    call_scope_enum.create(
        bind,
        checkfirst=True,
    )

    call_kind_enum.create(
        bind,
        checkfirst=True,
    )

    call_status_enum.create(
        bind,
        checkfirst=True,
    )

    participant_state_enum.create(
        bind,
        checkfirst=True,
    )

    screen_share_state_enum.create(
        bind,
        checkfirst=True,
    )

    op.create_table(
        "realtime_calls",
        sa.Column(
            "id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),
        sa.Column(
            "scope",
            call_scope_enum,
            nullable=False,
        ),
        sa.Column(
            "conversation_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=True,
        ),
        sa.Column(
            "channel_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=True,
        ),
        sa.Column(
            "started_by_user_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),
        sa.Column(
            "kind",
            call_kind_enum,
            nullable=False,
        ),
        sa.Column(
            "status",
            call_status_enum,
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
            "started_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=True,
        ),
        sa.Column(
            "ended_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=True,
        ),
        sa.Column(
            "ended_by_user_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint(
            "id"
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
            name=(
                "ck_realtime_call_scope_target"
            ),
        ),
    )

    op.create_index(
        "ix_realtime_calls_conversation_id",
        "realtime_calls",
        ["conversation_id"],
    )

    op.create_index(
        "ix_realtime_calls_channel_id",
        "realtime_calls",
        ["channel_id"],
    )

    op.create_index(
        "ix_realtime_calls_started_by_user_id",
        "realtime_calls",
        ["started_by_user_id"],
    )

    op.create_index(
        "ix_realtime_calls_status",
        "realtime_calls",
        ["status"],
    )

    op.create_index(
        "ix_realtime_calls_conversation_status",
        "realtime_calls",
        [
            "conversation_id",
            "status",
        ],
    )

    op.create_index(
        "ix_realtime_calls_channel_status",
        "realtime_calls",
        [
            "channel_id",
            "status",
        ],
    )

    op.create_table(
        "realtime_call_participants",
        sa.Column(
            "id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),
        sa.Column(
            "call_id",
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
            "state",
            participant_state_enum,
            nullable=False,
        ),
        sa.Column(
            "microphone_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text(
                "true"
            ),
        ),
        sa.Column(
            "camera_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text(
                "false"
            ),
        ),
        sa.Column(
            "screen_share_state",
            screen_share_state_enum,
            nullable=False,
        ),
        sa.Column(
            "joined_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=True,
        ),
        sa.Column(
            "left_at",
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
        sa.PrimaryKeyConstraint(
            "id"
        ),
        sa.UniqueConstraint(
            "call_id",
            "user_id",
            name=(
                "uq_realtime_call_participant_user"
            ),
        ),
    )

    op.create_index(
        "ix_realtime_call_participants_call_id",
        "realtime_call_participants",
        ["call_id"],
    )

    op.create_index(
        "ix_realtime_call_participants_user_id",
        "realtime_call_participants",
        ["user_id"],
    )

    op.create_index(
        "ix_realtime_call_participants_state",
        "realtime_call_participants",
        ["state"],
    )

    op.create_index(
        "ix_realtime_call_participants_call_state",
        "realtime_call_participants",
        [
            "call_id",
            "state",
        ],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_realtime_call_participants_call_state",
        table_name=(
            "realtime_call_participants"
        ),
    )

    op.drop_index(
        "ix_realtime_call_participants_state",
        table_name=(
            "realtime_call_participants"
        ),
    )

    op.drop_index(
        "ix_realtime_call_participants_user_id",
        table_name=(
            "realtime_call_participants"
        ),
    )

    op.drop_index(
        "ix_realtime_call_participants_call_id",
        table_name=(
            "realtime_call_participants"
        ),
    )

    op.drop_table(
        "realtime_call_participants"
    )

    op.drop_index(
        "ix_realtime_calls_channel_status",
        table_name="realtime_calls",
    )

    op.drop_index(
        "ix_realtime_calls_conversation_status",
        table_name="realtime_calls",
    )

    op.drop_index(
        "ix_realtime_calls_status",
        table_name="realtime_calls",
    )

    op.drop_index(
        "ix_realtime_calls_started_by_user_id",
        table_name="realtime_calls",
    )

    op.drop_index(
        "ix_realtime_calls_channel_id",
        table_name="realtime_calls",
    )

    op.drop_index(
        "ix_realtime_calls_conversation_id",
        table_name="realtime_calls",
    )

    op.drop_table(
        "realtime_calls"
    )

    bind = op.get_bind()

    screen_share_state_enum.drop(
        bind,
        checkfirst=True,
    )

    participant_state_enum.drop(
        bind,
        checkfirst=True,
    )

    call_status_enum.drop(
        bind,
        checkfirst=True,
    )

    call_kind_enum.drop(
        bind,
        checkfirst=True,
    )

    call_scope_enum.drop(
        bind,
        checkfirst=True,
    )