from __future__ import annotations

from app.modules.shifts.publication_models import (
    SchedulePublicationDay,
)
from app.modules.shifts.publication_snapshot import (
    SchedulePublicationSnapshotService,
)


def test_snapshot_table_name():
    assert (
        SchedulePublicationDay
        .__tablename__
        == "schedule_publication_days"
    )


def test_snapshot_has_required_columns():
    columns = {
        column.name
        for column
        in (
            SchedulePublicationDay
            .__table__
            .columns
        )
    }

    required = {
        "id",
        "publication_id",
        "employee_id",
        "schedule_date",
        "source",
        "shift_id",
        "timezone",
        "start_time",
        "end_time",
        "break_minutes",
        "scheduled_minutes",
        "payable_minutes",
        "is_working_day",
        "exception_id",
        "is_holiday",
        "holiday_id",
        "holiday_name",
        "holiday_treatment",
        "created_at",
    }

    assert required.issubset(
        columns
    )


def test_publication_fk_exists():
    column = (
        SchedulePublicationDay
        .__table__
        .c
        .publication_id
    )

    foreign_keys = list(
        column.foreign_keys
    )

    assert len(
        foreign_keys
    ) == 1

    assert (
        foreign_keys[0]
        .target_fullname
        == "schedule_publications.id"
    )


def test_snapshot_service_has_publish():
    assert hasattr(
        SchedulePublicationSnapshotService,
        "publish",
    )


def test_snapshot_service_has_resolve():
    assert hasattr(
        SchedulePublicationSnapshotService,
        "resolve_day",
    )


def test_snapshot_service_has_published_lookup():
    assert hasattr(
        SchedulePublicationSnapshotService,
        "get_published_day",
    )