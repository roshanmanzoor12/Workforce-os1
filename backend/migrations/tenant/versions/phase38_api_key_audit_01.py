"""Add the tenant API key audit outbox."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "phase38_api_key_audit_01"
down_revision = "phase37_api_keys_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "api_key_audit_outbox",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "actor_user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "key_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "action",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "replacement_key_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "delivered_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_api_key_audit_outbox_delivery",
        "api_key_audit_outbox",
        ["workspace_id", "delivered_at", "occurred_at", "id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_api_key_audit_outbox_delivery",
        table_name="api_key_audit_outbox",
    )
    op.drop_table("api_key_audit_outbox")