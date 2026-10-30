from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "l2g3h4i5j6k7"

down_revision: (
    str
    | Sequence[str]
    | None
) = "k1f2g3h4i5j6"

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


# =========================================================
# ENUM TYPES
# =========================================================
#
# SQLAlchemy Enum(PythonEnum) persists enum MEMBER NAMES
# by default.
#
# Therefore database enum values intentionally use:
#
# EMPLOYEE / TEAM
# OFF_DAY / CUSTOM_SHIFT
# DRAFT / PUBLISHED / CANCELLED
# PAID / UNPAID
#
# Python/API enum .value remains lowercase.
# =========================================================


shift_assignment_target_type = (
    postgresql.ENUM(
        "EMPLOYEE",
        "TEAM",
        name=(
            "shift_assignment_target_type"
        ),
        create_type=False,
    )
)


schedule_exception_type = (
    postgresql.ENUM(
        "OFF_DAY",
        "CUSTOM_SHIFT",
        name=(
            "schedule_exception_type"
        ),
        create_type=False,
    )
)


schedule_publication_status = (
    postgresql.ENUM(
        "DRAFT",
        "PUBLISHED",
        "CANCELLED",
        name=(
            "schedule_publication_status"
        ),
        create_type=False,
    )
)


holiday_treatment = (
    postgresql.ENUM(
        "PAID",
        "UNPAID",
        name="holiday_treatment",
        create_type=False,
    )
)


# =========================================================
# UPGRADE
# =========================================================


def upgrade() -> None:
    bind = op.get_bind()

    # -----------------------------------------------------
    # ENUMS
    # -----------------------------------------------------

    shift_assignment_target_type.create(
        bind,
        checkfirst=True,
    )

    schedule_exception_type.create(
        bind,
        checkfirst=True,
    )

    schedule_publication_status.create(
        bind,
        checkfirst=True,
    )

    holiday_treatment.create(
        bind,
        checkfirst=True,
    )

    # -----------------------------------------------------
    # SHIFT TEMPLATES
    # -----------------------------------------------------

    op.create_table(
        "shift_templates",

        sa.Column(
            "id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),

        sa.Column(
            "name",
            sa.String(
                length=120
            ),
            nullable=False,
        ),

        sa.Column(
            "timezone",
            sa.String(
                length=64
            ),
            nullable=False,
        ),

        sa.Column(
            "start_time",
            sa.Time(),
            nullable=False,
        ),

        sa.Column(
            "end_time",
            sa.Time(),
            nullable=False,
        ),

        sa.Column(
            "break_minutes",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "standard_paid_minutes",
            sa.Integer(),
            nullable=True,
        ),

        sa.Column(
            "grace_before_minutes",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "grace_after_minutes",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "overtime_after_minutes",
            sa.Integer(),
            nullable=True,
        ),

        sa.Column(
            "is_overnight",
            sa.Boolean(),
            nullable=False,
        ),

        sa.Column(
            "is_active",
            sa.Boolean(),
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

        sa.PrimaryKeyConstraint(
            "id",
        ),

        sa.UniqueConstraint(
            "name",
            name=(
                "uq_shift_templates_name"
            ),
        ),
    )

    op.create_index(
        "ix_shift_templates_active",
        "shift_templates",
        [
            "is_active",
        ],
        unique=False,
    )

    # -----------------------------------------------------
    # SHIFT WORKING DAYS
    # -----------------------------------------------------

    op.create_table(
        "shift_working_days",

        sa.Column(
            "id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),

        sa.Column(
            "shift_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),

        sa.Column(
            "weekday",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "is_working_day",
            sa.Boolean(),
            nullable=False,
        ),

        sa.ForeignKeyConstraint(
            [
                "shift_id",
            ],
            [
                "shift_templates.id",
            ],
            ondelete="CASCADE",
        ),

        sa.PrimaryKeyConstraint(
            "id",
        ),

        sa.UniqueConstraint(
            "shift_id",
            "weekday",
            name=(
                "uq_shift_working_days_"
                "shift_weekday"
            ),
        ),
    )

    op.create_index(
        "ix_shift_working_days_shift",
        "shift_working_days",
        [
            "shift_id",
        ],
        unique=False,
    )

    # -----------------------------------------------------
    # SHIFT ASSIGNMENTS
    # -----------------------------------------------------

    op.create_table(
        "shift_assignments",

        sa.Column(
            "id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),

        sa.Column(
            "shift_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),

        sa.Column(
            "target_type",
            shift_assignment_target_type,
            nullable=False,
        ),

        sa.Column(
            "target_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),

        sa.Column(
            "effective_from",
            sa.Date(),
            nullable=False,
        ),

        sa.Column(
            "effective_to",
            sa.Date(),
            nullable=True,
        ),

        sa.Column(
            "priority",
            sa.Integer(),
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
            [
                "shift_id",
            ],
            [
                "shift_templates.id",
            ],
            ondelete="RESTRICT",
        ),

        sa.PrimaryKeyConstraint(
            "id",
        ),
    )

    op.create_index(
        "ix_shift_assignments_target",
        "shift_assignments",
        [
            "target_type",
            "target_id",
        ],
        unique=False,
    )

    op.create_index(
        "ix_shift_assignments_effective",
        "shift_assignments",
        [
            "effective_from",
            "effective_to",
        ],
        unique=False,
    )

    # -----------------------------------------------------
    # SCHEDULE EXCEPTIONS
    # -----------------------------------------------------

    op.create_table(
        "schedule_exceptions",

        sa.Column(
            "id",
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
            "exception_date",
            sa.Date(),
            nullable=False,
        ),

        sa.Column(
            "exception_type",
            schedule_exception_type,
            nullable=False,
        ),

        sa.Column(
            "custom_start_time",
            sa.Time(),
            nullable=True,
        ),

        sa.Column(
            "custom_end_time",
            sa.Time(),
            nullable=True,
        ),

        sa.Column(
            "break_minutes",
            sa.Integer(),
            nullable=True,
        ),

        sa.Column(
            "reason",
            sa.String(
                length=500
            ),
            nullable=True,
        ),

        sa.Column(
            "created_by_user_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=True,
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

        sa.PrimaryKeyConstraint(
            "id",
        ),

        sa.UniqueConstraint(
            "employee_id",
            "exception_date",
            name=(
                "uq_schedule_exception_"
                "employee_date"
            ),
        ),
    )

    op.create_index(
        "ix_schedule_exceptions_date",
        "schedule_exceptions",
        [
            "exception_date",
        ],
        unique=False,
    )

    op.create_index(
        "ix_schedule_exceptions_employee_id",
        "schedule_exceptions",
        [
            "employee_id",
        ],
        unique=False,
    )

    # -----------------------------------------------------
    # SCHEDULE PUBLICATIONS
    # -----------------------------------------------------

    op.create_table(
        "schedule_publications",

        sa.Column(
            "id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),

        sa.Column(
            "period_start",
            sa.Date(),
            nullable=False,
        ),

        sa.Column(
            "period_end",
            sa.Date(),
            nullable=False,
        ),

        sa.Column(
            "status",
            schedule_publication_status,
            nullable=False,
        ),

        sa.Column(
            "published_by_user_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=True,
        ),

        sa.Column(
            "published_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=True,
        ),

        sa.Column(
            "note",
            sa.String(
                length=500
            ),
            nullable=True,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=False,
        ),

        sa.PrimaryKeyConstraint(
            "id",
        ),
    )

    op.create_index(
        "ix_schedule_publications_range",
        "schedule_publications",
        [
            "period_start",
            "period_end",
        ],
        unique=False,
    )

    # -----------------------------------------------------
    # HOLIDAYS
    # -----------------------------------------------------

    op.create_table(
        "holidays",

        sa.Column(
            "id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),

        sa.Column(
            "holiday_date",
            sa.Date(),
            nullable=False,
        ),

        sa.Column(
            "name",
            sa.String(
                length=160
            ),
            nullable=False,
        ),

        sa.Column(
            "treatment",
            holiday_treatment,
            nullable=False,
        ),

        sa.Column(
            "region",
            sa.String(
                length=120
            ),
            nullable=True,
        ),

        sa.Column(
            "description",
            sa.String(
                length=500
            ),
            nullable=True,
        ),

        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
        ),

        sa.Column(
            "created_by_user_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=True,
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

        sa.PrimaryKeyConstraint(
            "id",
        ),

        sa.UniqueConstraint(
            "holiday_date",
            "name",
            name=(
                "uq_holidays_date_name"
            ),
        ),
    )

    op.create_index(
        "ix_holidays_date_active",
        "holidays",
        [
            "holiday_date",
            "is_active",
        ],
        unique=False,
    )


# =========================================================
# DOWNGRADE
# =========================================================


def downgrade() -> None:
    bind = op.get_bind()

    # -----------------------------------------------------
    # HOLIDAYS
    # -----------------------------------------------------

    op.drop_index(
        "ix_holidays_date_active",
        table_name="holidays",
    )

    op.drop_table(
        "holidays"
    )

    # -----------------------------------------------------
    # PUBLICATIONS
    # -----------------------------------------------------

    op.drop_index(
        "ix_schedule_publications_range",
        table_name=(
            "schedule_publications"
        ),
    )

    op.drop_table(
        "schedule_publications"
    )

    # -----------------------------------------------------
    # EXCEPTIONS
    # -----------------------------------------------------

    op.drop_index(
        "ix_schedule_exceptions_employee_id",
        table_name=(
            "schedule_exceptions"
        ),
    )

    op.drop_index(
        "ix_schedule_exceptions_date",
        table_name=(
            "schedule_exceptions"
        ),
    )

    op.drop_table(
        "schedule_exceptions"
    )

    # -----------------------------------------------------
    # ASSIGNMENTS
    # -----------------------------------------------------

    op.drop_index(
        "ix_shift_assignments_effective",
        table_name=(
            "shift_assignments"
        ),
    )

    op.drop_index(
        "ix_shift_assignments_target",
        table_name=(
            "shift_assignments"
        ),
    )

    op.drop_table(
        "shift_assignments"
    )

    # -----------------------------------------------------
    # WORKING DAYS
    # -----------------------------------------------------

    op.drop_index(
        "ix_shift_working_days_shift",
        table_name=(
            "shift_working_days"
        ),
    )

    op.drop_table(
        "shift_working_days"
    )

    # -----------------------------------------------------
    # SHIFT TEMPLATE
    # -----------------------------------------------------

    op.drop_index(
        "ix_shift_templates_active",
        table_name=(
            "shift_templates"
        ),
    )

    op.drop_table(
        "shift_templates"
    )

    # -----------------------------------------------------
    # ENUMS
    # -----------------------------------------------------

    holiday_treatment.drop(
        bind,
        checkfirst=True,
    )

    schedule_publication_status.drop(
        bind,
        checkfirst=True,
    )

    schedule_exception_type.drop(
        bind,
        checkfirst=True,
    )

    shift_assignment_target_type.drop(
        bind,
        checkfirst=True,
    )