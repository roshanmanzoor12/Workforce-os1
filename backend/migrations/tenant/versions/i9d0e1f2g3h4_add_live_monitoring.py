from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "i9d0e1f2g3h4"
down_revision = "h8c9d0e1f2g3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "screenshot_capture_requests",

        sa.Column(
            "id",
            sa.Uuid(),
            nullable=False,
        ),

        sa.Column(
            "device_id",
            sa.Uuid(),
            nullable=False,
        ),

        sa.Column(
            "employee_id",
            sa.Uuid(),
            nullable=False,
        ),

        sa.Column(
            "requested_by_user_id",
            sa.Uuid(),
            nullable=False,
        ),

        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default="pending",
        ),

        sa.Column(
            "reason",
            sa.String(length=500),
            nullable=True,
        ),

        sa.Column(
            "visible_indicator_required",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),

        sa.Column(
            "consent_required",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),

        sa.Column(
            "consent_confirmed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),

        sa.Column(
            "requested_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),

        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),

        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),

        sa.Column(
            "storage_object_key",
            sa.String(length=1024),
            nullable=True,
        ),

        sa.Column(
            "sha256",
            sa.String(length=64),
            nullable=True,
        ),

        sa.Column(
            "width",
            sa.Integer(),
            nullable=True,
        ),

        sa.Column(
            "height",
            sa.Integer(),
            nullable=True,
        ),

        sa.Column(
            "metadata_json",
            postgresql.JSONB(
                astext_type=sa.Text()
            ),
            nullable=False,
            server_default=sa.text(
                "'{}'::jsonb"
            ),
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),

        sa.PrimaryKeyConstraint(
            "id"
        ),
    )

    op.create_index(
        "ix_screenshot_capture_requests_device",
        "screenshot_capture_requests",
        [
            "device_id",
            "requested_at",
        ],
        unique=False,
    )

    op.create_index(
        "ix_screenshot_capture_requests_employee",
        "screenshot_capture_requests",
        [
            "employee_id",
            "requested_at",
        ],
        unique=False,
    )

    op.create_index(
        "ix_screenshot_capture_requests_status",
        "screenshot_capture_requests",
        [
            "status",
            "expires_at",
        ],
        unique=False,
    )

    op.create_table(
        "live_screen_sessions",

        sa.Column(
            "id",
            sa.Uuid(),
            nullable=False,
        ),

        sa.Column(
            "device_id",
            sa.Uuid(),
            nullable=False,
        ),

        sa.Column(
            "employee_id",
            sa.Uuid(),
            nullable=False,
        ),

        sa.Column(
            "requested_by_user_id",
            sa.Uuid(),
            nullable=False,
        ),

        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default="requested",
        ),

        sa.Column(
            "reason",
            sa.String(length=500),
            nullable=True,
        ),

        sa.Column(
            "consent_required",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),

        sa.Column(
            "visible_indicator_required",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),

        sa.Column(
            "accepted_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),

        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),

        sa.Column(
            "ended_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),

        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),

        sa.Column(
            "transport",
            sa.String(length=50),
            nullable=False,
            server_default="webrtc",
        ),

        sa.Column(
            "session_channel",
            sa.String(length=255),
            nullable=True,
        ),

        sa.Column(
            "end_reason",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "metadata_json",
            postgresql.JSONB(
                astext_type=sa.Text()
            ),
            nullable=False,
            server_default=sa.text(
                "'{}'::jsonb"
            ),
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),

        sa.PrimaryKeyConstraint(
            "id"
        ),
    )

    op.create_index(
        "ix_live_screen_sessions_device",
        "live_screen_sessions",
        [
            "device_id",
            "created_at",
        ],
        unique=False,
    )

    op.create_index(
        "ix_live_screen_sessions_employee",
        "live_screen_sessions",
        [
            "employee_id",
            "created_at",
        ],
        unique=False,
    )

    op.create_index(
        "ix_live_screen_sessions_status",
        "live_screen_sessions",
        [
            "status",
            "expires_at",
        ],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_live_screen_sessions_status",
        table_name="live_screen_sessions",
    )

    op.drop_index(
        "ix_live_screen_sessions_employee",
        table_name="live_screen_sessions",
    )

    op.drop_index(
        "ix_live_screen_sessions_device",
        table_name="live_screen_sessions",
    )

    op.drop_table(
        "live_screen_sessions"
    )

    op.drop_index(
        "ix_screenshot_capture_requests_status",
        table_name=(
            "screenshot_capture_requests"
        ),
    )

    op.drop_index(
        "ix_screenshot_capture_requests_employee",
        table_name=(
            "screenshot_capture_requests"
        ),
    )

    op.drop_index(
        "ix_screenshot_capture_requests_device",
        table_name=(
            "screenshot_capture_requests"
        ),
    )

    op.drop_table(
        "screenshot_capture_requests"
    )