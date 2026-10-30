from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.modules.activity.models import (
    ActivityStateEvent,
)
from app.modules.work_sessions.activity_hook import (
    on_activity_state_event,
)
from app.modules.work_sessions.models import (
    WorkSession,
)


@pytest.mark.asyncio
async def test_activity_hook_creates_work_session() -> None:
    now = datetime(
        2026,
        8,
        28,
        16,
        0,
        tzinfo=timezone.utc,
    )

    device_id = uuid4()

    event = ActivityStateEvent(
        id=uuid4(),
        device_id=device_id,
        employee_id=None,
        state="active",
        idle_seconds=0,
        last_input_at=now,
        observed_at=now,
        received_at=now,
        created_at=now,
    )

    session = MagicMock()

    added_objects: list[object] = []

    def capture_add(
        instance: object,
    ) -> None:
        added_objects.append(
            instance
        )

    async def emulate_flush() -> None:
        """
        Emulate the relevant SQLAlchemy flush behavior.

        WorkSession.id uses a Python-side SQLAlchemy default. In a real
        AsyncSession the UUID is populated during INSERT/flush. Because this
        unit test uses mocks rather than a real database, we reproduce that
        one behavior explicitly.
        """

        for instance in added_objects:
            if (
                isinstance(
                    instance,
                    WorkSession,
                )
                and instance.id is None
            ):
                instance.id = uuid4()

    session.add = MagicMock(
        side_effect=capture_add
    )

    execute_result = MagicMock()

    execute_result.scalar_one_or_none.return_value = (
        None
    )

    session.execute = AsyncMock(
        return_value=execute_result
    )

    session.flush = AsyncMock(
        side_effect=emulate_flush
    )

    session.commit = AsyncMock()

    session.refresh = AsyncMock()

    result = await on_activity_state_event(
        session,
        event,
    )

    assert result.session_id is not None

    assert result.created is True

    assert (
        result.closed_previous_session
        is False
    )

    assert result.ignored_event is False

    assert result.status == "open"

    assert result.current_state == "active"

    assert result.active_seconds == 0

    assert result.idle_seconds == 0

    assert result.total_seconds == 0

    session.execute.assert_awaited_once()

    session.add.assert_called_once()

    session.flush.assert_awaited_once()

    session.commit.assert_awaited_once()

    assert len(
        added_objects
    ) == 1

    created_session = (
        added_objects[0]
    )

    assert isinstance(
        created_session,
        WorkSession,
    )

    assert (
        created_session.id
        == result.session_id
    )

    assert (
        created_session.device_id
        == device_id
    )

    assert (
        created_session.employee_id
        is None
    )

    assert (
        created_session.status
        == "open"
    )

    assert (
        created_session.current_state
        == "active"
    )

    assert (
        created_session.started_at
        == now
    )

    assert (
        created_session.last_observed_at
        == now
    )

    assert (
        created_session.active_seconds
        == 0
    )

    assert (
        created_session.idle_seconds
        == 0
    )