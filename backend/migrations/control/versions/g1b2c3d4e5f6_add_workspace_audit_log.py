from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import (
    postgresql,
)


revision = "g1b2c3d4e5f6"
down_revision = "f1a2b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workspace_audit_events",

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
            "actor_user_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=True,
        ),

        sa.Column(
            "category",
            sa.String(
                length=100
            ),
            nullable=False,
        ),

        sa.Column(
            "action",
            sa.String(
                length=150
            ),
            nullable=False,
        ),

        sa.Column(
            "outcome",
            sa.String(
                length=20
            ),
            nullable=False,
            server_default="success",
        ),

        sa.Column(
            "severity",
            sa.String(
                length=20
            ),
            nullable=False,
            server_default="info",
        ),

        sa.Column(
            "target_type",
            sa.String(
                length=100
            ),
            nullable=True,
        ),

        sa.Column(
            "target_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=True,
        ),

        sa.Column(
            "target_label",
            sa.String(
                length=255
            ),
            nullable=True,
        ),

        sa.Column(
            "message",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "request_id",
            sa.String(
                length=100
            ),
            nullable=True,
        ),

        sa.Column(
            "ip_address",
            sa.String(
                length=64
            ),
            nullable=True,
        ),

        sa.Column(
            "user_agent",
            sa.String(
                length=1000
            ),
            nullable=True,
        ),

        sa.Column(
            "event_data",
            postgresql.JSONB(
                astext_type=sa.Text()
            ),
            nullable=False,
            server_default=sa.text(
                "'{}'::jsonb"
            ),
        ),

        sa.Column(
            "occurred_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=False,
            server_default=sa.func.now(),
        ),

        sa.PrimaryKeyConstraint(
            "id",
            name="pk_workspace_audit_events",
        ),
    )

    op.create_index(
        "ix_wsa_workspace_id",
        "workspace_audit_events",
        [
            "workspace_id",
        ],
        unique=False,
    )

    op.create_index(
        "ix_wsa_actor_user_id",
        "workspace_audit_events",
        [
            "actor_user_id",
        ],
        unique=False,
    )

    op.create_index(
        "ix_wsa_category",
        "workspace_audit_events",
        [
            "category",
        ],
        unique=False,
    )

    op.create_index(
        "ix_wsa_action_single",
        "workspace_audit_events",
        [
            "action",
        ],
        unique=False,
    )

    op.create_index(
        "ix_wsa_request_id",
        "workspace_audit_events",
        [
            "request_id",
        ],
        unique=False,
    )

    op.create_index(
        "ix_wsa_workspace_time",
        "workspace_audit_events",
        [
            "workspace_id",
            "occurred_at",
        ],
        unique=False,
    )

    op.create_index(
        "ix_wsa_actor_time",
        "workspace_audit_events",
        [
            "actor_user_id",
            "occurred_at",
        ],
        unique=False,
    )

    op.create_index(
        "ix_wsa_action",
        "workspace_audit_events",
        [
            "workspace_id",
            "action",
        ],
        unique=False,
    )

    op.create_index(
        "ix_wsa_target",
        "workspace_audit_events",
        [
            "workspace_id",
            "target_type",
            "target_id",
        ],
        unique=False,
    )

    # =====================================================
    # DATABASE-LEVEL IMMUTABILITY
    # =====================================================

    op.execute(
        """
        CREATE FUNCTION
            workforce_prevent_audit_event_mutation()
        RETURNS trigger
        AS $$
        BEGIN
            RAISE EXCEPTION
                'workspace_audit_events is append-only';
        END;
        $$
        LANGUAGE plpgsql;
        """
    )

    op.execute(
        """
        CREATE TRIGGER
            trg_workspace_audit_events_immutable
        BEFORE UPDATE OR DELETE
        ON workspace_audit_events
        FOR EACH ROW
        EXECUTE FUNCTION
            workforce_prevent_audit_event_mutation();
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TRIGGER IF EXISTS
            trg_workspace_audit_events_immutable
        ON workspace_audit_events;
        """
    )

    op.drop_index(
        "ix_wsa_target",
        table_name=(
            "workspace_audit_events"
        ),
    )

    op.drop_index(
        "ix_wsa_action",
        table_name=(
            "workspace_audit_events"
        ),
    )

    op.drop_index(
        "ix_wsa_actor_time",
        table_name=(
            "workspace_audit_events"
        ),
    )

    op.drop_index(
        "ix_wsa_workspace_time",
        table_name=(
            "workspace_audit_events"
        ),
    )

    op.drop_index(
        "ix_wsa_request_id",
        table_name=(
            "workspace_audit_events"
        ),
    )

    op.drop_index(
        "ix_wsa_action_single",
        table_name=(
            "workspace_audit_events"
        ),
    )

    op.drop_index(
        "ix_wsa_category",
        table_name=(
            "workspace_audit_events"
        ),
    )

    op.drop_index(
        "ix_wsa_actor_user_id",
        table_name=(
            "workspace_audit_events"
        ),
    )

    op.drop_index(
        "ix_wsa_workspace_id",
        table_name=(
            "workspace_audit_events"
        ),
    )

    op.drop_table(
        "workspace_audit_events"
    )

    op.execute(
        """
        DROP FUNCTION IF EXISTS
            workforce_prevent_audit_event_mutation();
        """
    )