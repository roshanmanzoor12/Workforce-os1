"""Persist Company/Agency workspace style.

Revision ID: ws_type_20261020_01
Revises: av20261016_01
"""
from alembic import op
import sqlalchemy as sa

revision = 'ws_type_20261020_01'
down_revision = 'av20261016_01'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('workspaces', sa.Column('workspace_type', sa.String(20), nullable=False, server_default='company'))
    op.create_check_constraint(op.f('ck_workspaces_workspace_type'), 'workspaces', "workspace_type IN ('company', 'agency')")


def downgrade():
    op.drop_constraint(op.f('ck_workspaces_workspace_type'), 'workspaces', type_='check')
    op.drop_column('workspaces', 'workspace_type')
