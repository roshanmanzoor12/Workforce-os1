from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.modules.work_sessions.reconciliation import (
    WorkSessionReconciliationService,
)


@pytest.mark.asyncio
async def test_reconciliation_returns_zero_when_no_events() -> None:
    session = MagicMock()

    result = MagicMock()

    result.scalars.return_value.all.return_value = (
        []
    )

    session.execute = AsyncMock(
        return_value=result
    )

    service = (
        WorkSessionReconciliationService(
            session
        )
    )

    processed = await service.reconcile_device(
        uuid4()
    )

    assert processed == 0

    session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_reconciliation_rejects_invalid_limit() -> None:
    session = MagicMock()

    service = (
        WorkSessionReconciliationService(
            session
        )
    )

    with pytest.raises(
        ValueError,
        match="limit",
    ):
        await service.reconcile_device(
            uuid4(),
            limit=0,
        )


@pytest.mark.asyncio
async def test_reconciliation_rejects_naive_observed_from() -> None:
    session = MagicMock()

    service = (
        WorkSessionReconciliationService(
            session
        )
    )

    naive_datetime = datetime(
        2026,
        8,
        28,
        12,
        0,
    )

    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        await service.reconcile_device(
            uuid4(),
            observed_from=naive_datetime,
        )


@pytest.mark.asyncio
async def test_reconciliation_accepts_timezone_aware_filter() -> None:
    session = MagicMock()

    result = MagicMock()

    result.scalars.return_value.all.return_value = (
        []
    )

    session.execute = AsyncMock(
        return_value=result
    )

    service = (
        WorkSessionReconciliationService(
            session
        )
    )

    observed_from = datetime(
        2026,
        8,
        28,
        12,
        0,
        tzinfo=timezone.utc,
    )

    processed = await service.reconcile_device(
        uuid4(),
        observed_from=observed_from,
    )

    assert processed == 0