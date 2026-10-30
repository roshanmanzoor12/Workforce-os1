from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import ResourceNotFound
from app.modules.devices.heartbeat_presence import (
    DEVICE_ONLINE_TIMEOUT_SECONDS,
)
from app.modules.devices.heartbeat_presence_service import (
    DevicePresenceService,
)
from app.modules.devices.models import (
    DEVICE_STATUS_ACTIVE,
)


def make_device(
    *,
    last_seen_at: datetime | None,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        device_uuid=uuid.uuid4(),
        status=DEVICE_STATUS_ACTIVE,
        is_active=True,
        last_seen_at=last_seen_at,
    )


def make_session(
    device: SimpleNamespace | None,
) -> AsyncMock:
    session = AsyncMock()

    result = MagicMock()

    result.scalar_one_or_none.return_value = (
        device
    )

    session.execute.return_value = result

    return session


@pytest.mark.asyncio
async def test_presence_service_returns_online_device() -> None:
    now = datetime.now(
        timezone.utc
    )

    device = make_device(
        last_seen_at=(
            now
            - timedelta(
                seconds=10
            )
        )
    )

    session = make_session(
        device
    )

    service = DevicePresenceService(
        session
    )

    response = await service.get_presence(
        device_id=device.id,
        device_uuid=device.device_uuid,
    )

    assert (
        response.device_uuid
        == device.device_uuid
    )

    assert response.is_online is True

    assert (
        response.last_seen_at
        == device.last_seen_at
    )

    assert response.offline_since is None

    assert (
        response.online_timeout_seconds
        == DEVICE_ONLINE_TIMEOUT_SECONDS
    )


@pytest.mark.asyncio
async def test_presence_service_returns_offline_device() -> None:
    now = datetime.now(
        timezone.utc
    )

    last_seen_at = (
        now
        - timedelta(
            seconds=(
                DEVICE_ONLINE_TIMEOUT_SECONDS
                + 30
            )
        )
    )

    device = make_device(
        last_seen_at=last_seen_at
    )

    session = make_session(
        device
    )

    service = DevicePresenceService(
        session
    )

    response = await service.get_presence(
        device_id=device.id,
        device_uuid=device.device_uuid,
    )

    assert response.is_online is False

    assert (
        response.last_seen_at
        == last_seen_at
    )

    assert (
        response.offline_since
        == (
            last_seen_at
            + timedelta(
                seconds=(
                    DEVICE_ONLINE_TIMEOUT_SECONDS
                )
            )
        )
    )


@pytest.mark.asyncio
async def test_presence_service_returns_never_seen_device() -> None:
    device = make_device(
        last_seen_at=None
    )

    session = make_session(
        device
    )

    service = DevicePresenceService(
        session
    )

    response = await service.get_presence(
        device_id=device.id,
        device_uuid=device.device_uuid,
    )

    assert response.is_online is False

    assert response.last_seen_at is None

    assert response.offline_since is None


@pytest.mark.asyncio
async def test_presence_service_rejects_missing_device() -> None:
    session = make_session(
        None
    )

    service = DevicePresenceService(
        session
    )

    with pytest.raises(
        ResourceNotFound
    ):
        await service.get_presence(
            device_id=uuid.uuid4(),
            device_uuid=uuid.uuid4(),
        )