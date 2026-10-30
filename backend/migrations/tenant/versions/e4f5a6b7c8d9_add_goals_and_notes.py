"""add goals and notes

Revision ID: e4f5a6b7c8d9
Revises: d3e4f5a6b7c8
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "e4f5a6b7c8d9"
down_revision = "d3e4f5a6b7c8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "goals",
        sa.Column(
            "owner_employee_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),
        sa.Column(
            "title",
            sa.String(
                length=200
            ),
            nullable=False,
        ),
        sa.Column(
            "description",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "status",
            sa.String(
                length=32
            ),
            nullable=False,
        ),
        sa.Column(
            "priority",
            sa.String(
                length=32
            ),
            nullable=False,
        ),
        sa.Column(
            "progress_percent",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "start_date",
            sa.Date(),
            nullable=True,
        ),
        sa.Column(
            "due_date",
            sa.Date(),
            nullable=True,
        ),
        sa.Column(
            "completed_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=True,
        ),
        sa.Column(
            "id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=False,
        ),
        sa.CheckConstraint(
            (
                "status IN "
                "('active', 'completed', "
                "'cancelled', 'archived')"
            ),
            name="ck_goals_status",
        ),
        sa.CheckConstraint(
            (
                "priority IN "
                "('low', 'medium', 'high')"
            ),
            name="ck_goals_priority",
        ),
        sa.CheckConstraint(
            (
                "progress_percent >= 0 "
                "AND progress_percent <= 100"
            ),
            name="ck_goals_progress_percent",
        ),
        sa.ForeignKeyConstraint(
            ["owner_employee_id"],
            ["employees.id"],
            name="fk_goals_owner_employee_id_employees",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name="pk_goals",
        ),
    )

    op.create_index(
        "ix_goals_owner_employee",
        "goals",
        ["owner_employee_id"],
        unique=False,
    )

    op.create_index(
        "ix_goals_status",
        "goals",
        ["status"],
        unique=False,
    )

    op.create_index(
        "ix_goals_due_date",
        "goals",
        ["due_date"],
        unique=False,
    )

    op.create_table(
        "notes",
        sa.Column(
            "owner_employee_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),
        sa.Column(
            "title",
            sa.String(
                length=200
            ),
            nullable=False,
        ),
        sa.Column(
            "content",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "is_pinned",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "is_archived",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["owner_employee_id"],
            ["employees.id"],
            name="fk_notes_owner_employee_id_employees",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name="pk_notes",
        ),
    )

    op.create_index(
        "ix_notes_owner_employee",
        "notes",
        ["owner_employee_id"],
        unique=False,
    )

    op.create_index(
        "ix_notes_is_archived",
        "notes",
        ["is_archived"],
        unique=False,
    )

    op.create_index(
        "ix_notes_is_pinned",
        "notes",
        ["is_pinned"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_notes_is_pinned",
        table_name="notes",
    )

    op.drop_index(
        "ix_notes_is_archived",
        table_name="notes",
    )

    op.drop_index(
        "ix_notes_owner_employee",
        table_name="notes",
    )

    op.drop_table(
        "notes"
    )

    op.drop_index(
        "ix_goals_due_date",
        table_name="goals",
    )

    op.drop_index(
        "ix_goals_status",
        table_name="goals",
    )

    op.drop_index(
        "ix_goals_owner_employee",
        table_name="goals",
    )

    op.drop_table(
        "goals"
    )