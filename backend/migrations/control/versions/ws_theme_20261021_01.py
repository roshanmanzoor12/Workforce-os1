"""Persist independent workspace theme colors.

Revision ID: ws_theme_20261021_01
Revises: ws_type_20261020_01
"""
from alembic import op
import sqlalchemy as sa

revision = "ws_theme_20261021_01"
down_revision = "ws_type_20261020_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("workspaces", sa.Column("primary_color", sa.String(7), nullable=False, server_default="#2563EB"))
    op.add_column("workspaces", sa.Column("accent_color", sa.String(7), nullable=False, server_default="#F59E0B"))
    op.create_check_constraint("ck_workspaces_primary_color_format", "workspaces", "primary_color ~ '^#[0-9A-Fa-f]{6}$'")
    op.create_check_constraint("ck_workspaces_accent_color_format", "workspaces", "accent_color ~ '^#[0-9A-Fa-f]{6}$'")


def downgrade() -> None:
    op.drop_constraint("ck_workspaces_accent_color_format", "workspaces", type_="check")
    op.drop_constraint("ck_workspaces_primary_color_format", "workspaces", type_="check")
    op.drop_column("workspaces", "accent_color")
    op.drop_column("workspaces", "primary_color")
