
"""Create WorkforceOS monitoring consent, events and live sessions.

Revision ID: wfos_monitoring_01
Revises: phase38_api_key_audit_01

This migration adds the legacy monitoring API storage tables.
It does not modify the existing live_monitoring or desktop agent tables.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op
from sqlalchemy.dialects import postgresql


# ============================================================
# ALEMBIC REVISION
# ============================================================

revision = "wfos_monitoring_01"

down_revision = "phase38_api_key_audit_01"

branch_labels = None

depends_on = None


# ============================================================
# SHARED TENANT COLUMNS
# ============================================================

def standard_columns() -> list[sa.Column]:
    return [
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
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
    ]


# ============================================================
# UPGRADE
# ============================================================

def upgrade() -> None:

    # --------------------------------------------------------
    # MONITORING CONSENT
    # --------------------------------------------------------

    op.create_table(
        "monitoring_consents",
        *standard_columns(),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "granted",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "policy_version",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "granted_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "revoked_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name="pk_monitoring_consents",
        ),
        sa.UniqueConstraint(
            "user_id",
            name="uq_monitoring_consents_user",
        ),
    )

    op.create_index(
        "ix_monitoring_consents_created_at",
        "monitoring_consents",
        ["created_at"],
        unique=False,
    )

    # --------------------------------------------------------
    # MONITORING EVENTS
    # --------------------------------------------------------

    op.create_table(
        "monitoring_events",
        *standard_columns(),
        sa.Column(
            "kind",
            sa.String(length=48),
            nullable=False,
        ),
        sa.Column(
            "device_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "employee_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "payload",
            sa.JSON(),
            nullable=False,
        ),
        sa.Column(
            "captured_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "source",
            sa.String(length=32),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name="pk_monitoring_events",
        ),
    )

    op.create_index(
        "ix_monitoring_events_created_at",
        "monitoring_events",
        ["created_at"],
        unique=False,
    )

    op.create_index(
        "ix_monitoring_events_kind_created",
        "monitoring_events",
        ["kind", "created_at"],
        unique=False,
    )

    op.create_index(
        "ix_monitoring_events_device_created",
        "monitoring_events",
        ["device_id", "created_at"],
        unique=False,
    )

    # --------------------------------------------------------
    # MONITORING LIVE SESSIONS
    # --------------------------------------------------------

    op.create_table(
        "monitoring_live_sessions",
        *standard_columns(),
        sa.Column(
            "device_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "requested_by_user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=24),
            nullable=False,
        ),
        sa.Column(
            "consent_id",
            postgresql.UUID(as_uuid=True),
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
            "end_reason",
            sa.Text(),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name="pk_monitoring_live_sessions",
        ),
    )

    op.create_index(
        "ix_monitoring_live_sessions_created_at",
        "monitoring_live_sessions",
        ["created_at"],
        unique=False,
    )

    op.create_index(
        "ix_monitoring_live_sessions_status",
        "monitoring_live_sessions",
        ["status"],
        unique=False,
    )


# ============================================================
# DOWNGRADE
# ============================================================

def downgrade() -> None:
    # Downgrading removes monitoring data.
    # Never run downgrade on a populated production tenant
    # without a verified backup and data-retention approval.

    op.drop_index(
        "ix_monitoring_live_sessions_status",
        table_name="monitoring_live_sessions",
    )

    op.drop_index(
        "ix_monitoring_live_sessions_created_at",
        table_name="monitoring_live_sessions",
    )

    op.drop_table(
        "monitoring_live_sessions"
    )

    op.drop_index(
        "ix_monitoring_events_device_created",
        table_name="monitoring_events",
    )

    op.drop_index(
        "ix_monitoring_events_kind_created",
        table_name="monitoring_events",
    )

    op.drop_index(
        "ix_monitoring_events_created_at",
        table_name="monitoring_events",
    )

    op.drop_table(
        "monitoring_events"
    )

    op.drop_index(
        "ix_monitoring_consents_created_at",
        table_name="monitoring_consents",
    )

    op.drop_table(
        "monitoring_consents"
    )
