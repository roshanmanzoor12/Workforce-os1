from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.modules.work_sessions.models import (
    WORK_SESSION_STATE_ACTIVE,
    WORK_SESSION_STATUS_CLOSED,
    WORK_SESSION_STATUS_OPEN,
    WorkSession,
)
from app.modules.work_sessions.recovery import (
    WorkSessionRecoveryService,
)


@pytest.mark.asyncio
async def test_recovery_closes_stale_open_session() -> None:
    now = datetime(
        2026,
        8,
        28,
        16,
        30,
        tzinfo=timezone.utc,
    )

    last_observed_at = (
        now
        - timedelta(
            minutes=20
        )
    )

    work_session = WorkSession(
        id=uuid4(),
        device_id=uuid4(),
        employee_id=None,
        status=WORK_SESSION_STATUS_OPEN,
        current_state=WORK_SESSION_STATE_ACTIVE,
        started_at=(
            last_observed_at
            - timedelta(
                minutes=10
            )
        ),
        ended_at=None,
        last_observed_at=last_observed_at,
        active_seconds=600,
        idle_seconds=0,
    )

    db_session = MagicMock()

    result = MagicMock()

    result.scalars.return_value.all.return_value = [
        work_session
    ]

    db_session.execute = AsyncMock(
        return_value=result
    )

    db_session.commit = AsyncMock()

    service = WorkSessionRecoveryService(
        db_session,
        stale_session_seconds=600,
    )

    closed_count = await service.close_stale(
        now=now
    )

    assert closed_count == 1

    assert (
        work_session.status
        == WORK_SESSION_STATUS_CLOSED
    )

    assert (
        work_session.ended_at
        == last_observed_at
    )

    db_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_recovery_does_not_close_recent_session() -> None:
    now = datetime(
        2026,
        8,
        28,
        16,
        30,
        tzinfo=timezone.utc,
    )

    db_session = MagicMock()

    result = MagicMock()

    result.scalars.return_value.all.return_value = []

    db_session.execute = AsyncMock(
        return_value=result
    )

    db_session.commit = AsyncMock()

    service = WorkSessionRecoveryService(
        db_session,
        stale_session_seconds=600,
    )

    closed_count = await service.close_stale(
        now=now
    )

    assert closed_count == 0

    db_session.commit.assert_not_awaited()


def test_recovery_rejects_naive_datetime() -> None:
    db_session = MagicMock()

    service = WorkSessionRecoveryService(
        db_session
    )

    naive_now = datetime(
        2026,
        8,
        28,
        16,
        30,
    )

    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        import asyncio

        asyncio.run(
            service.close_stale(
                now=naive_now
            )
        )