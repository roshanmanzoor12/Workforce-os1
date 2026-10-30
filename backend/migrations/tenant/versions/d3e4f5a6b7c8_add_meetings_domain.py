"""add meetings domain

Revision ID: d3e4f5a6b7c8
Revises: c2d3e4f5a6b7
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# =========================================================
# ALEMBIC REVISION IDENTIFIERS
# =========================================================

revision = "d3e4f5a6b7c8"
down_revision = "c2d3e4f5a6b7"
branch_labels = None
depends_on = None


# =========================================================
# UPGRADE
# =========================================================


def upgrade() -> None:
    op.create_table(
        "meetings",
        sa.Column(
            "title",
            sa.String(length=200),
            nullable=False,
        ),
        sa.Column(
            "description",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "meeting_type",
            sa.String(length=32),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
        ),
        sa.Column(
            "scheduled_start_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "scheduled_end_at",
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
            "location",
            sa.String(length=500),
            nullable=True,
        ),
        sa.Column(
            "created_by_user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
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
        sa.CheckConstraint(
            (
                "status IN "
                "('scheduled', 'active', "
                "'completed', 'cancelled')"
            ),
            name="ck_meetings_status",
        ),
        sa.CheckConstraint(
            (
                "meeting_type IN "
                "('video', 'voice', 'in_person')"
            ),
            name="ck_meetings_type",
        ),
        sa.CheckConstraint(
            (
                "scheduled_end_at IS NULL "
                "OR scheduled_end_at > scheduled_start_at"
            ),
            name="ck_meetings_end_after_start",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name="pk_meetings",
        ),
    )

    op.create_index(
        "ix_meetings_status",
        "meetings",
        ["status"],
        unique=False,
    )

    op.create_index(
        "ix_meetings_start",
        "meetings",
        ["scheduled_start_at"],
        unique=False,
    )

    op.create_index(
        "ix_meetings_created_by_user",
        "meetings",
        ["created_by_user_id"],
        unique=False,
    )

    op.create_table(
        "meeting_participants",
        sa.Column(
            "meeting_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "employee_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "participant_role",
            sa.String(length=32),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
        ),
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
        sa.CheckConstraint(
            (
                "participant_role IN "
                "('organizer', 'participant')"
            ),
            name="ck_meeting_participants_role",
        ),
        sa.CheckConstraint(
            (
                "status IN "
                "('invited', 'accepted', 'declined')"
            ),
            name="ck_meeting_participants_status",
        ),
        sa.ForeignKeyConstraint(
            ["meeting_id"],
            ["meetings.id"],
            name="fk_meeting_participants_meeting_id_meetings",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["employee_id"],
            ["employees.id"],
            name="fk_meeting_participants_employee_id_employees",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name="pk_meeting_participants",
        ),
        sa.UniqueConstraint(
            "meeting_id",
            "employee_id",
            name="uq_meeting_participants_meeting_employee",
        ),
    )

    op.create_index(
        "ix_meeting_participants_meeting",
        "meeting_participants",
        ["meeting_id"],
        unique=False,
    )

    op.create_index(
        "ix_meeting_participants_employee",
        "meeting_participants",
        ["employee_id"],
        unique=False,
    )


# =========================================================
# DOWNGRADE
# =========================================================


def downgrade() -> None:
    op.drop_index(
        "ix_meeting_participants_employee",
        table_name="meeting_participants",
    )

    op.drop_index(
        "ix_meeting_participants_meeting",
        table_name="meeting_participants",
    )

    op.drop_table(
        "meeting_participants"
    )

    op.drop_index(
        "ix_meetings_created_by_user",
        table_name="meetings",
    )

    op.drop_index(
        "ix_meetings_start",
        table_name="meetings",
    )

    op.drop_index(
        "ix_meetings_status",
        table_name="meetings",
    )

    op.drop_table(
        "meetings"
    )