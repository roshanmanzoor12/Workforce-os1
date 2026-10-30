from __future__ import annotations

from app.modules.holidays.models import (
    Holiday,
)
from app.modules.shifts.models import (
    ScheduleException,
    SchedulePublication,
    ShiftAssignment,
    ShiftTemplate,
    ShiftWorkingDay,
)


def test_shift_table_names():
    assert (
        ShiftTemplate.__tablename__
        == "shift_templates"
    )

    assert (
        ShiftWorkingDay.__tablename__
        == "shift_working_days"
    )

    assert (
        ShiftAssignment.__tablename__
        == "shift_assignments"
    )

    assert (
        ScheduleException.__tablename__
        == "schedule_exceptions"
    )

    assert (
        SchedulePublication.__tablename__
        == "schedule_publications"
    )


def test_holiday_table_name():
    assert (
        Holiday.__tablename__
        == "holidays"
    )


def test_shift_template_primary_key():
    columns = {
        column.name:
        column
        for column
        in ShiftTemplate.__table__.columns
    }

    assert "id" in columns
    assert columns["id"].primary_key


def test_assignment_required_columns():
    columns = {
        column.name
        for column
        in ShiftAssignment.__table__.columns
    }

    required = {
        "id",
        "shift_id",
        "target_type",
        "target_id",
        "effective_from",
        "effective_to",
        "priority",
        "created_at",
        "updated_at",
    }

    assert required.issubset(
        columns
    )


def test_exception_required_columns():
    columns = {
        column.name
        for column
        in ScheduleException
        .__table__
        .columns
    }

    required = {
        "id",
        "employee_id",
        "exception_date",
        "exception_type",
        "custom_start_time",
        "custom_end_time",
        "break_minutes",
        "reason",
        "created_by_user_id",
        "created_at",
        "updated_at",
    }

    assert required.issubset(
        columns
    )


def test_publication_required_columns():
    columns = {
        column.name
        for column
        in SchedulePublication
        .__table__
        .columns
    }

    required = {
        "id",
        "period_start",
        "period_end",
        "status",
        "published_by_user_id",
        "published_at",
        "note",
        "created_at",
    }

    assert required.issubset(
        columns
    )


def test_holiday_required_columns():
    columns = {
        column.name
        for column
        in Holiday.__table__.columns
    }

    required = {
        "id",
        "holiday_date",
        "name",
        "treatment",
        "region",
        "description",
        "is_active",
        "created_by_user_id",
        "created_at",
        "updated_at",
    }

    assert required.issubset(
        columns
    )