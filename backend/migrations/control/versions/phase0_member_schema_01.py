"""Align membership metadata with the application model."""
from alembic import op
import sqlalchemy as sa

revision = "phase0_member_schema_01"
down_revision = "phase38_member_scopes_01"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("workspace_memberships"):
        raise RuntimeError(
            "Control database membership table is missing."
        )

    columns = {
        item["name"]
        for item in inspector.get_columns("workspace_memberships")
    }

    required = {
        "role_key",
        "workspace_id",
        "user_id",
        "joined_at",
        "invited_by_user_id",
        "invited_at",
    }

    if not required.issubset(columns):
        raise RuntimeError(
            "Membership schema needs earlier migrations first."
        )

    if "source" not in columns:
        op.add_column(
            "workspace_memberships",
            sa.Column("source", sa.String(32), nullable=True),
        )

        op.execute(sa.text("""
            UPDATE workspace_memberships AS m
            SET source = CASE
                WHEN EXISTS (
                    SELECT 1
                    FROM workspaces AS w
                    WHERE w.id = m.workspace_id
                      AND w.created_by_user_id = m.user_id
                ) THEN 'CREATOR'
                WHEN m.invited_by_user_id IS NOT NULL
                  OR m.invited_at IS NOT NULL
                    THEN 'INVITATION'
                ELSE 'ADMIN'
            END
        """))

        op.alter_column(
            "workspace_memberships",
            "source",
            existing_type=sa.String(32),
            nullable=False,
        )

    if "activated_at" not in columns:
        op.add_column(
            "workspace_memberships",
            sa.Column(
                "activated_at",
                sa.DateTime(timezone=True),
                nullable=True,
            ),
        )

        op.execute(sa.text("""
            UPDATE workspace_memberships
            SET activated_at = joined_at
            WHERE joined_at IS NOT NULL
        """))


def downgrade():
    raise RuntimeError(
        "This repair preserves existing columns and is forward-only. "
        "Use a reviewed follow-up migration to reverse it."
    )
