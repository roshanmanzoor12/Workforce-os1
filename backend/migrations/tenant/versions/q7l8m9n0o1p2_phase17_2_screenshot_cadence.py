from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# =========================================================
# ALEMBIC IDENTIFIERS
# =========================================================


revision = "q7l8m9n0o1p2"

down_revision = "p6k7l8m9n0o1"

branch_labels = None

depends_on = None


# =========================================================
# UPGRADE
# =========================================================


def upgrade() -> None:
    op.add_column(
        "monitoring_admin_policies",
        sa.Column(
            "screenshot_interval_seconds",
            sa.Integer(),
            nullable=False,
            server_default=sa.text(
                "300"
            ),
        ),
    )

    op.create_check_constraint(
        (
            "ck_monitoring_admin_policy_"
            "screenshot_interval_seconds"
        ),
        "monitoring_admin_policies",
        (
            "screenshot_interval_seconds "
            ">= 1"
        ),
    )


# =========================================================
# DOWNGRADE
# =========================================================


def downgrade() -> None:
    op.drop_constraint(
        (
            "ck_monitoring_admin_policy_"
            "screenshot_interval_seconds"
        ),
        "monitoring_admin_policies",
        type_="check",
    )

    op.drop_column(
        "monitoring_admin_policies",
        "screenshot_interval_seconds",
    )