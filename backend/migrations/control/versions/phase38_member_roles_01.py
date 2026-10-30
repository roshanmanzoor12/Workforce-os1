"""Create additional workspace membership role assignments."""

from alembic import op
import sqlalchemy as sa


revision = "phase38_member_roles_01"
down_revision = "h2c3d4e5f6g7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workspace_membership_role_assignments",
        sa.Column(
            "membership_id",
            sa.Uuid(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "role_key",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "custom_role_id",
            sa.Uuid(as_uuid=True),
            nullable=True,
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
            "role_key",
            name="pk_workspace_membership_role_assignments",
        ),
        sa.ForeignKeyConstraint(
            ["membership_id"],
            ["workspace_memberships.id"],
            ondelete="CASCADE",
            name="fk_member_role_assignments_membership",
        ),
        sa.ForeignKeyConstraint(
            ["custom_role_id"],
            ["workspace_custom_roles.id"],
            ondelete="RESTRICT",
            name="fk_member_role_assignments_custom_role",
        ),
        sa.ForeignKeyConstraint(
            ["granted_by_user_id"],
            ["users.id"],
            ondelete="RESTRICT",
            name="fk_member_role_assignments_grantor",
        ),
        sa.CheckConstraint(
            "role_key <> 'owner'",
            name="ck_member_role_assignments_no_owner",
        ),
        sa.CheckConstraint(
            """
            (
                role_key IN ('admin', 'manager', 'member', 'client')
                AND custom_role_id IS NULL
            )
            OR
            (
                role_key NOT IN (
                    'owner', 'admin', 'manager', 'member', 'client'
                )
                AND custom_role_id IS NOT NULL
            )
            """,
            name="ck_member_role_assignments_role_reference",
        ),
    )

    op.create_index(
        "ix_member_role_assignments_custom_role",
        "workspace_membership_role_assignments",
        ["custom_role_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_member_role_assignments_custom_role",
        table_name="workspace_membership_role_assignments",
    )
    op.drop_table("workspace_membership_role_assignments")