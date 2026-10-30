"""Create workspace API key records."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "phase37_api_keys_01"
down_revision = 'q7l8m9n0o1p2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workspace_api_keys",
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
            "created_by_user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "name",
            sa.String(length=120),
            nullable=False,
        ),
        sa.Column(
            "key_prefix",
            sa.String(length=48),
            nullable=False,
        ),
        sa.Column(
            "secret_hash",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "scopes",
            sa.JSON(),
            nullable=False,
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "revoked_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "revoked_by_user_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "last_used_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name="pk_workspace_api_keys",
        ),
    )

    op.create_index(
        "ix_workspace_api_keys_workspace_created",
        "workspace_api_keys",
        ["workspace_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_workspace_api_keys_workspace_created",
        table_name="workspace_api_keys",
    )
    op.drop_table("workspace_api_keys")
