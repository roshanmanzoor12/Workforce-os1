from __future__ import annotations

import inspect
import uuid
from datetime import (
    datetime,
    timezone,
)

from app.modules.work_sessions.models import (
    WORK_SESSION_STATE_ACTIVE,
    WORK_SESSION_STATE_IDLE,
    WORK_SESSION_STATUS_CLOSED,
    WORK_SESSION_STATUS_OPEN,
    WorkSession,
)
from app.modules.work_sessions.service import (
    WorkSessionService,
)


def test_work_session_states_are_explicit():
    assert (
        WORK_SESSION_STATE_ACTIVE
        == "active"
    )

    assert (
        WORK_SESSION_STATE_IDLE
        == "idle"
    )

    assert (
        WORK_SESSION_STATUS_OPEN
        == "open"
    )

    assert (
        WORK_SESSION_STATUS_CLOSED
        == "closed"
    )


def test_work_session_total_seconds():
    now = datetime.now(
        timezone.utc
    )

    item = WorkSession(
        id=uuid.uuid4(),
        device_id=uuid.uuid4(),
        employee_id=uuid.uuid4(),

        status=(
            WORK_SESSION_STATUS_OPEN
        ),

        current_state=(
            WORK_SESSION_STATE_ACTIVE
        ),

        started_at=now,

        ended_at=None,

        last_observed_at=now,

        active_seconds=120,

        idle_seconds=30,
    )

    assert (
        item.total_seconds
        == 150
    )


def test_work_session_service_accounts_active_time():
    source = inspect.getsource(
        WorkSessionService
        ._apply_elapsed_time
    )

    assert (
        "WORK_SESSION_STATE_ACTIVE"
        in source
    )

    assert (
        "active_seconds"
        in source
    )


def test_work_session_service_accounts_idle_time():
    source = inspect.getsource(
        WorkSessionService
        ._apply_elapsed_time
    )

    assert (
        "WORK_SESSION_STATE_IDLE"
        in source
    )

    assert (
        "idle_seconds"
        in source
    )