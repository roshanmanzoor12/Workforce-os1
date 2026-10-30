from __future__ import annotations

from unittest.mock import (
    AsyncMock,
    MagicMock,
)
from uuid import uuid4

import pytest

from app.modules.app_tracking.query_service import (
    AppTrackingQueryService,
)


@pytest.mark.asyncio
async def test_latest_observation_returns_none() -> None:
    session = MagicMock()

    result = MagicMock()

    result.scalar_one_or_none.return_value = (
        None
    )

    session.execute = AsyncMock(
        return_value=result
    )

    service = AppTrackingQueryService(
        session
    )

    observation = (
        await service.get_latest_observation(
            uuid4()
        )
    )

    assert observation is None

    session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_current_interval_returns_none() -> None:
    session = MagicMock()

    result = MagicMock()

    result.scalar_one_or_none.return_value = (
        None
    )

    session.execute = AsyncMock(
        return_value=result
    )

    service = AppTrackingQueryService(
        session
    )

    interval = (
        await service.get_current_interval(
            uuid4()
        )
    )

    assert interval is None

    session.execute.assert_awaited_once()