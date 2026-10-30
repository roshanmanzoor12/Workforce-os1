"""Per-workspace permission overrides for non-owner built-in roles.

Revision ID: ws_builtin_roles_20261021_01
Revises: ws_theme_20261021_01
"""
from alembic import op
import sqlalchemy as sa

revision = "ws_builtin_roles_20261021_01"
down_revision = "ws_theme_20261021_01"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "workspace_builtin_role_overrides",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("workspace_id", sa.Uuid(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role_key", sa.String(64), nullable=False),
        sa.Column("permissions", sa.JSON(), nullable=False),
        sa.UniqueConstraint("workspace_id", "role_key", name="uq_builtin_role_override_workspace_key"),
        sa.CheckConstraint("role_key IN ('admin', 'manager', 'member', 'client')", name="ck_builtin_role_override_role_key"),
    )


def downgrade():
    op.drop_table("workspace_builtin_role_overrides")
