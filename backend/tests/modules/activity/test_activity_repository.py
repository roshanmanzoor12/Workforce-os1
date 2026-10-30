from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.activity.models import (
    ActivityStateEvent,
)
from app.modules.activity.repository import (
    ActivityRepository,
)


def make_session() -> MagicMock:
    session = MagicMock()

    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()

    return session


@pytest.mark.asyncio
async def test_repository_creates_event() -> None:
    session = make_session()

    repository = ActivityRepository(
        session
    )

    now = datetime.now(
        timezone.utc
    )

    device_id = uuid.uuid4()
    employee_id = uuid.uuid4()

    event = await repository.create_event(
        device_id=device_id,
        employee_id=employee_id,
        state="active",
        idle_seconds=3,
        last_input_at=now,
        observed_at=now,
        received_at=now,
    )

    assert isinstance(
        event,
        ActivityStateEvent,
    )

    assert event.device_id == device_id
    assert event.employee_id == employee_id
    assert event.state == "active"
    assert event.idle_seconds == 3

    session.add.assert_called_once_with(
        event
    )

    session.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_repository_commits() -> None:
    session = make_session()

    repository = ActivityRepository(
        session
    )

    await repository.commit()

    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_repository_rolls_back() -> None:
    session = make_session()

    repository = ActivityRepository(
        session
    )

    await repository.rollback()

    session.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_repository_refreshes_event() -> None:
    session = make_session()

    repository = ActivityRepository(
        session
    )

    event = MagicMock(
        spec=ActivityStateEvent
    )

    result = await repository.refresh(
        event
    )

    session.refresh.assert_awaited_once_with(
        event
    )

    assert result is event


@pytest.mark.asyncio
async def test_repository_latest_device_event() -> None:
    session = make_session()

    scalar_result = MagicMock()

    expected_event = MagicMock(
        spec=ActivityStateEvent
    )

    scalar_result.scalar_one_or_none.return_value = (
        expected_event
    )

    session.execute.return_value = (
        scalar_result
    )

    repository = ActivityRepository(
        session
    )

    result = await repository.get_latest_for_device(
        device_id=uuid.uuid4()
    )

    assert result is expected_event

    session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_repository_latest_employee_event() -> None:
    session = make_session()

    scalar_result = MagicMock()

    expected_event = MagicMock(
        spec=ActivityStateEvent
    )

    scalar_result.scalar_one_or_none.return_value = (
        expected_event
    )

    session.execute.return_value = (
        scalar_result
    )

    repository = ActivityRepository(
        session
    )

    result = await repository.get_latest_for_employee(
        employee_id=uuid.uuid4()
    )

    assert result is expected_event

    session.execute.assert_awaited_once()