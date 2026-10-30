from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.modules.work_sessions.models import (
    WORK_SESSION_STATE_ACTIVE,
    WORK_SESSION_STATUS_OPEN,
    WorkSession,
)


def test_work_session_table_name() -> None:
    assert WorkSession.__tablename__ == "work_sessions"


def test_work_session_expected_columns() -> None:
    columns = {
        column.name
        for column
        in WorkSession.__table__.columns
    }

    assert columns == {
        "id",
        "device_id",
        "employee_id",
        "status",
        "current_state",
        "started_at",
        "ended_at",
        "last_observed_at",
        "active_seconds",
        "idle_seconds",
        "created_at",
        "updated_at",
    }


def test_work_session_constraints_exist() -> None:
    constraint_names = {
        constraint.name
        for constraint
        in WorkSession.__table__.constraints
        if constraint.name is not None
    }

    assert any(
        name.endswith(
            "ck_work_sessions_status"
        )
        for name in constraint_names
    )

    assert any(
        name.endswith(
            "ck_work_sessions_current_state"
        )
        for name in constraint_names
    )

    assert any(
        name.endswith(
            "ck_work_sessions_active_seconds_nonnegative"
        )
        for name in constraint_names
    )

    assert any(
        name.endswith(
            "ck_work_sessions_idle_seconds_nonnegative"
        )
        for name in constraint_names
    )

    assert any(
        name.endswith(
            "ck_work_sessions_valid_time_range"
        )
        for name in constraint_names
    )


def test_work_session_indexes_exist() -> None:
    index_names = {
        index.name
        for index
        in WorkSession.__table__.indexes
    }

    assert (
        "ix_work_sessions_device_started_at"
        in index_names
    )

    assert (
        "ix_work_sessions_employee_started_at"
        in index_names
    )

    assert (
        "ix_work_sessions_status_last_observed_at"
        in index_names
    )

    assert (
        "uq_work_sessions_one_open_per_device"
        in index_names
    )


def test_total_seconds_property() -> None:
    now = datetime.now(
        timezone.utc
    )

    work_session = WorkSession(
        id=uuid4(),
        device_id=uuid4(),
        employee_id=None,
        status=WORK_SESSION_STATUS_OPEN,
        current_state=WORK_SESSION_STATE_ACTIVE,
        started_at=now,
        ended_at=None,
        last_observed_at=now,
        active_seconds=120,
        idle_seconds=45,
    )

    assert work_session.total_seconds == 165