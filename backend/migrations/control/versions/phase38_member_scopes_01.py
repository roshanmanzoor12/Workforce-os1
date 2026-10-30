"""Create explicit membership department and team scope grants."""

from alembic import op
import sqlalchemy as sa


revision = "phase38_member_scopes_01"
down_revision = "phase38_member_roles_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workspace_membership_scope_grants",
        sa.Column(
            "membership_id",
            sa.Uuid(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "scope_type",
            sa.String(length=32),
            nullable=False,
        ),
        sa.Column(
            "resource_id",
            sa.Uuid(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "granted_by_user_id",
            sa.Uuid(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint(
            "membership_id",
            "scope_type",
            "resource_id",
            name="pk_workspace_membership_scope_grants",
        ),
        sa.ForeignKeyConstraint(
            ["membership_id"],
            ["workspace_memberships.id"],
            name="fk_membership_scope_grants_membership",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["granted_by_user_id"],
            ["users.id"],
            name="fk_membership_scope_grants_grantor",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "scope_type IN ('department', 'team')",
            name="scope_type_supported",
        ),
    )

    op.create_index(
        "ix_membership_scope_grants_grantor",
        "workspace_membership_scope_grants",
        ["granted_by_user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_membership_scope_grants_grantor",
        table_name="workspace_membership_scope_grants",
    )

    op.drop_table("workspace_membership_scope_grants")