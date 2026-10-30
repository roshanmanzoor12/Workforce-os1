from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.modules.activity.models import (
    ActivityStateEvent,
)
from app.modules.work_sessions.live_integration import (
    process_persisted_activity_event,
)
from app.modules.work_sessions.models import (
    WorkSession,
)


@pytest.mark.asyncio
async def test_process_persisted_activity_event_creates_session() -> None:
    now = datetime(
        2026,
        8,
        28,
        16,
        0,
        tzinfo=timezone.utc,
    )

    event_id = uuid4()

    event = ActivityStateEvent(
        id=event_id,
        device_id=uuid4(),
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
        for instance in added_objects:
            if (
                isinstance(
                    instance,
                    WorkSession,
                )
                and instance.id is None
            ):
                instance.id = uuid4()

    event_result = MagicMock()

    event_result.scalar_one_or_none.return_value = (
        event
    )

    open_session_result = MagicMock()

    open_session_result.scalar_one_or_none.return_value = (
        None
    )

    session.execute = AsyncMock(
        side_effect=[
            event_result,
            open_session_result,
        ]
    )

    session.add = MagicMock(
        side_effect=capture_add
    )

    session.flush = AsyncMock(
        side_effect=emulate_flush
    )

    session.commit = AsyncMock()

    result = await process_persisted_activity_event(
        session,
        event_id,
    )

    assert result.created is True

    assert result.ignored_event is False

    assert result.current_state == "active"

    assert result.active_seconds == 0

    assert result.idle_seconds == 0

    assert result.session_id is not None

    assert len(
        added_objects
    ) == 1

    created_session = added_objects[0]

    assert isinstance(
        created_session,
        WorkSession,
    )

    assert (
        created_session.device_id
        == event.device_id
    )


@pytest.mark.asyncio
async def test_process_persisted_activity_event_rejects_missing_event() -> None:
    session = MagicMock()

    result = MagicMock()

    result.scalar_one_or_none.return_value = (
        None
    )

    session.execute = AsyncMock(
        return_value=result
    )

    event_id = uuid4()

    with pytest.raises(
        RuntimeError,
        match="Activity event not found",
    ):
        await process_persisted_activity_event(
            session,
            event_id,
        )