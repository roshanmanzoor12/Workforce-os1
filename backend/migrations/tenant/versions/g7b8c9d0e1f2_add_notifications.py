from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import (
    postgresql,
)


revision = "g7b8c9d0e1f2"
down_revision = "f6a7b8c9d0e1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notifications",

        sa.Column(
            "id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),

        sa.Column(
            "recipient_user_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),

        sa.Column(
            "notification_type",
            sa.String(
                length=100
            ),
            nullable=False,
        ),

        sa.Column(
            "title",
            sa.String(
                length=255
            ),
            nullable=False,
        ),

        sa.Column(
            "body",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "priority",
            sa.String(
                length=20
            ),
            nullable=False,
            server_default="normal",
        ),

        sa.Column(
            "entity_type",
            sa.String(
                length=100
            ),
            nullable=True,
        ),

        sa.Column(
            "entity_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=True,
        ),

        sa.Column(
            "action_url",
            sa.String(
                length=1000
            ),
            nullable=True,
        ),

        sa.Column(
            "payload",
            postgresql.JSONB(
                astext_type=sa.Text()
            ),
            nullable=False,
            server_default=sa.text(
                "'{}'::jsonb"
            ),
        ),

        sa.Column(
            "read_at",
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
            server_default=sa.func.now(),
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=False,
            server_default=sa.func.now(),
        ),

        sa.PrimaryKeyConstraint(
            "id",
            name="pk_notifications",
        ),
    )

    op.create_index(
        "ix_notifications_recipient",
        "notifications",
        [
            "recipient_user_id",
        ],
        unique=False,
    )

    op.create_index(
        "ix_notifications_type",
        "notifications",
        [
            "notification_type",
        ],
        unique=False,
    )

    op.create_index(
        "ix_notif_user_created",
        "notifications",
        [
            "recipient_user_id",
            "created_at",
        ],
        unique=False,
    )

    op.create_index(
        "ix_notif_user_read",
        "notifications",
        [
            "recipient_user_id",
            "read_at",
        ],
        unique=False,
    )

    op.create_index(
        "ix_notif_entity",
        "notifications",
        [
            "entity_type",
            "entity_id",
        ],
        unique=False,
    )

    op.create_table(
        "notification_preferences",

        sa.Column(
            "id",
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
            "in_app_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),

        sa.Column(
            "email_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),

        sa.Column(
            "push_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),

        sa.Column(
            "sound_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),

        sa.Column(
            "digest_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),

        sa.Column(
            "digest_hour",
            sa.Integer(),
            nullable=False,
            server_default="8",
        ),

        sa.Column(
            "muted_types",
            postgresql.JSONB(
                astext_type=sa.Text()
            ),
            nullable=False,
            server_default=sa.text(
                "'[]'::jsonb"
            ),
        ),

        sa.Column(
            "created_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=False,
            server_default=sa.func.now(),
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=False,
            server_default=sa.func.now(),
        ),

        sa.PrimaryKeyConstraint(
            "id",
            name=(
                "pk_notification_preferences"
            ),
        ),

        sa.UniqueConstraint(
            "user_id",
            name="uq_notif_pref_user",
        ),
    )

    op.create_index(
        "ix_notif_pref_user",
        "notification_preferences",
        [
            "user_id",
        ],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_notif_pref_user",
        table_name=(
            "notification_preferences"
        ),
    )

    op.drop_table(
        "notification_preferences"
    )

    op.drop_index(
        "ix_notif_entity",
        table_name="notifications",
    )

    op.drop_index(
        "ix_notif_user_read",
        table_name="notifications",
    )

    op.drop_index(
        "ix_notif_user_created",
        table_name="notifications",
    )

    op.drop_index(
        "ix_notifications_type",
        table_name="notifications",
    )

    op.drop_index(
        "ix_notifications_recipient",
        table_name="notifications",
    )

    op.drop_table(
        "notifications"
    )