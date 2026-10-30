from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "j0e1f2g3h4i5"

down_revision = "i9d0e1f2g3h4"

branch_labels = None

depends_on = None


def upgrade() -> None:
    op.create_table(
        "voice_channel_calls",

        sa.Column(
            "id",
            sa.Uuid(),
            nullable=False,
        ),

        sa.Column(
            "channel_id",
            sa.Uuid(),
            nullable=False,
        ),

        sa.Column(
            "created_by_user_id",
            sa.Uuid(),
            nullable=False,
        ),

        sa.Column(
            "status",
            sa.String(
                length=32
            ),
            nullable=False,
            server_default="active",
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
            "ended_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=True,
        ),

        sa.PrimaryKeyConstraint(
            "id"
        ),
    )

    op.create_index(
        "uq_voice_channel_calls_active_channel",
        "voice_channel_calls",
        [
            "channel_id",
        ],
        unique=True,
        postgresql_where=sa.text(
            "status = 'active'"
        ),
    )

    op.create_index(
        "ix_voice_channel_calls_channel",
        "voice_channel_calls",
        [
            "channel_id",
            "created_at",
        ],
        unique=False,
    )

    op.create_table(
        "voice_channel_participants",

        sa.Column(
            "id",
            sa.Uuid(),
            nullable=False,
        ),

        sa.Column(
            "call_id",
            sa.Uuid(),
            nullable=False,
        ),

        sa.Column(
            "user_id",
            sa.Uuid(),
            nullable=False,
        ),

        sa.Column(
            "state",
            sa.String(
                length=32
            ),
            nullable=False,
            server_default="joined",
        ),

        sa.Column(
            "self_muted",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text(
                "false"
            ),
        ),

        sa.Column(
            "self_deafened",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text(
                "false"
            ),
        ),

        sa.Column(
            "server_muted",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text(
                "false"
            ),
        ),

        sa.Column(
            "server_deafened",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text(
                "false"
            ),
        ),

        sa.Column(
            "screen_sharing",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text(
                "false"
            ),
        ),

        sa.Column(
            "joined_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=False,
            server_default=sa.text(
                "now()"
            ),
        ),

        sa.Column(
            "left_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=True,
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

        sa.PrimaryKeyConstraint(
            "id"
        ),

        sa.UniqueConstraint(
            "call_id",
            "user_id",
            name=(
                "uq_voice_channel_participants_"
                "call_user"
            ),
        ),
    )

    op.create_index(
        "ix_voice_channel_participants_call_state",
        "voice_channel_participants",
        [
            "call_id",
            "state",
        ],
        unique=False,
    )

    op.create_index(
        "ix_voice_channel_participants_user",
        "voice_channel_participants",
        [
            "user_id",
        ],
        unique=False,
    )

    op.create_table(
        "voice_channel_bans",

        sa.Column(
            "id",
            sa.Uuid(),
            nullable=False,
        ),

        sa.Column(
            "channel_id",
            sa.Uuid(),
            nullable=False,
        ),

        sa.Column(
            "user_id",
            sa.Uuid(),
            nullable=False,
        ),

        sa.Column(
            "banned_by_user_id",
            sa.Uuid(),
            nullable=False,
        ),

        sa.Column(
            "reason",
            sa.Text(),
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
                "now()"
            ),
        ),

        sa.Column(
            "lifted_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=True,
        ),

        sa.PrimaryKeyConstraint(
            "id"
        ),

        sa.UniqueConstraint(
            "channel_id",
            "user_id",
            name=(
                "uq_voice_channel_bans_"
                "channel_user"
            ),
        ),
    )

    op.create_index(
        "ix_voice_channel_bans_channel_active",
        "voice_channel_bans",
        [
            "channel_id",
            "is_active",
        ],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_voice_channel_bans_channel_active",
        table_name="voice_channel_bans",
    )

    op.drop_table(
        "voice_channel_bans"
    )

    op.drop_index(
        "ix_voice_channel_participants_user",
        table_name=(
            "voice_channel_participants"
        ),
    )

    op.drop_index(
        "ix_voice_channel_participants_call_state",
        table_name=(
            "voice_channel_participants"
        ),
    )

    op.drop_table(
        "voice_channel_participants"
    )

    op.drop_index(
        "ix_voice_channel_calls_channel",
        table_name=(
            "voice_channel_calls"
        ),
    )

    op.drop_index(
        "uq_voice_channel_calls_active_channel",
        table_name=(
            "voice_channel_calls"
        ),
    )

    op.drop_table(
        "voice_channel_calls"
    )