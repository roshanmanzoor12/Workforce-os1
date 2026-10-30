from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "k1f2g3h4i5j6"

down_revision = "j0e1f2g3h4i5"

branch_labels = None

depends_on = None


def upgrade() -> None:
    op.create_table(
        "monitoring_admin_policies",

        sa.Column(
            "id",
            sa.Uuid(),
            nullable=False,
        ),

        sa.Column(
            "policy_key",
            sa.String(
                length=64
            ),
            nullable=False,
            server_default="default",
        ),

        sa.Column(
            "monitoring_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text(
                "true"
            ),
        ),

        sa.Column(
            "screenshots_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text(
                "true"
            ),
        ),

        sa.Column(
            "live_screen_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text(
                "true"
            ),
        ),

        sa.Column(
            "screen_share_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text(
                "true"
            ),
        ),

        sa.Column(
            "disclosure_required",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text(
                "true"
            ),
        ),

        sa.Column(
            "explicit_live_consent_required",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text(
                "true"
            ),
        ),

        sa.Column(
            "visible_live_indicator_required",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text(
                "true"
            ),
        ),

        sa.Column(
            "screenshot_retention_days",
            sa.Integer(),
            nullable=False,
            server_default="30",
        ),

        sa.Column(
            "live_session_max_minutes",
            sa.Integer(),
            nullable=False,
            server_default="60",
        ),

        sa.Column(
            "policy_version",
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),

        sa.Column(
            "policy_notice",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "updated_by_user_id",
            sa.Uuid(),
            nullable=True,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=False,
            server_default=sa.text(
                "now()"
            ),
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=False,
            server_default=sa.text(
                "now()"
            ),
        ),

        sa.CheckConstraint(
            "screenshot_retention_days >= 1 "
            "AND screenshot_retention_days <= 3650",
            name=(
                "ck_monitoring_admin_policy_"
                "screenshot_retention_days"
            ),
        ),

        sa.CheckConstraint(
            "live_session_max_minutes >= 1 "
            "AND live_session_max_minutes <= 480",
            name=(
                "ck_monitoring_admin_policy_"
                "live_session_max_minutes"
            ),
        ),

        sa.PrimaryKeyConstraint(
            "id"
        ),

        sa.UniqueConstraint(
            "policy_key",
            name=(
                "uq_monitoring_admin_"
                "policies_policy_key"
            ),
        ),
    )


def downgrade() -> None:
    op.drop_table(
        "monitoring_admin_policies"
    )