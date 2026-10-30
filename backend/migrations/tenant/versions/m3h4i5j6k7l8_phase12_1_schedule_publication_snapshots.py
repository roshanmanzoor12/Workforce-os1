from __future__ import annotations

from collections.abc import (
    Sequence,
)

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import (
    postgresql,
)


revision: str = (
    "m3h4i5j6k7l8"
)

down_revision: (
    str
    | Sequence[str]
    | None
) = "l2g3h4i5j6k7"

branch_labels: (
    str
    | Sequence[str]
    | None
) = None

depends_on: (
    str
    | Sequence[str]
    | None
) = None


def upgrade() -> None:
    op.create_table(
        "schedule_publication_days",

        sa.Column(
            "id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),

        sa.Column(
            "publication_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),

        sa.Column(
            "employee_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),

        sa.Column(
            "schedule_date",
            sa.Date(),
            nullable=False,
        ),

        sa.Column(
            "source",
            sa.String(
                length=64
            ),
            nullable=False,
        ),

        sa.Column(
            "shift_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=True,
        ),

        sa.Column(
            "timezone",
            sa.String(
                length=64
            ),
            nullable=True,
        ),

        sa.Column(
            "start_time",
            sa.Time(),
            nullable=True,
        ),

        sa.Column(
            "end_time",
            sa.Time(),
            nullable=True,
        ),

        sa.Column(
            "break_minutes",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),

        sa.Column(
            "scheduled_minutes",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),

        sa.Column(
            "payable_minutes",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),

        sa.Column(
            "is_working_day",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),

        sa.Column(
            "exception_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=True,
        ),

        sa.Column(
            "is_holiday",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),

        sa.Column(
            "holiday_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=True,
        ),

        sa.Column(
            "holiday_name",
            sa.String(
                length=160
            ),
            nullable=True,
        ),

        sa.Column(
            "holiday_treatment",
            sa.String(
                length=20
            ),
            nullable=True,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=False,
            server_default=sa.func.now(),
        ),

        sa.ForeignKeyConstraint(
            [
                "publication_id",
            ],
            [
                "schedule_publications.id",
            ],
            ondelete="CASCADE",
        ),

        sa.PrimaryKeyConstraint(
            "id",
        ),

        sa.UniqueConstraint(
            "publication_id",
            "employee_id",
            "schedule_date",
            name=(
                "uq_schedule_publication_day_"
                "publication_employee_date"
            ),
        ),
    )

    op.create_index(
        (
            "ix_schedule_publication_days_"
            "employee_date"
        ),
        "schedule_publication_days",
        [
            "employee_id",
            "schedule_date",
        ],
        unique=False,
    )

    op.create_index(
        (
            "ix_schedule_publication_days_"
            "publication"
        ),
        "schedule_publication_days",
        [
            "publication_id",
        ],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        (
            "ix_schedule_publication_days_"
            "publication"
        ),
        table_name=(
            "schedule_publication_days"
        ),
    )

    op.drop_index(
        (
            "ix_schedule_publication_days_"
            "employee_date"
        ),
        table_name=(
            "schedule_publication_days"
        ),
    )

    op.drop_table(
        "schedule_publication_days"
    )