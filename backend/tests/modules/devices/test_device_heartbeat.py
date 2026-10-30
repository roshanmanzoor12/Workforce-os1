from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.devices.heartbeat_schemas import (
    DeviceHeartbeatRequest,
)
from app.modules.devices.heartbeat_service import (
    DEFAULT_HEARTBEAT_INTERVAL_SECONDS,
    DeviceHeartbeatService,
)
from app.modules.devices.models import (
    DEVICE_STATUS_ACTIVE,
    DEVICE_STATUS_DISABLED,
    DEVICE_STATUS_OFFLINE,
    DEVICE_STATUS_REVOKED,
)


def make_device(
    *,
    status: str = DEVICE_STATUS_ACTIVE,
    is_active: bool = True,
    first_seen_at: datetime | None = None,
    last_seen_at: datetime | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        device_uuid=uuid.uuid4(),
        status=status,
        is_active=is_active,
        hostname="OLD-HOSTNAME",
        agent_version="0.0.1",
        first_seen_at=first_seen_at,
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
async def test_heartbeat_updates_last_seen() -> None:
    device = make_device()

    session = make_session(
        device
    )

    service = DeviceHeartbeatService(
        session
    )

    before = datetime.now(
        timezone.utc
    )

    response = await service.record_heartbeat(
        device_id=device.id,
        device_uuid=device.device_uuid,
        payload=DeviceHeartbeatRequest(),
    )

    after = datetime.now(
        timezone.utc
    )

    assert device.last_seen_at is not None

    assert (
        before
        <= device.last_seen_at
        <= after
    )

    assert (
        response.device_uuid
        == device.device_uuid
    )

    assert (
        response.status
        == DEVICE_STATUS_ACTIVE
    )

    assert (
        response.next_heartbeat_seconds
        == DEFAULT_HEARTBEAT_INTERVAL_SECONDS
    )

    session.commit.assert_awaited_once()

    session.refresh.assert_awaited_once_with(
        device
    )


@pytest.mark.asyncio
async def test_first_heartbeat_sets_first_seen() -> None:
    device = make_device(
        first_seen_at=None,
        last_seen_at=None,
    )

    session = make_session(
        device
    )

    service = DeviceHeartbeatService(
        session
    )

    await service.record_heartbeat(
        device_id=device.id,
        device_uuid=device.device_uuid,
        payload=DeviceHeartbeatRequest(),
    )

    assert device.first_seen_at is not None

    assert device.last_seen_at is not None


@pytest.mark.asyncio
async def test_heartbeat_restores_offline_device() -> None:
    device = make_device(
        status=DEVICE_STATUS_OFFLINE
    )

    session = make_session(
        device
    )

    service = DeviceHeartbeatService(
        session
    )

    response = await service.record_heartbeat(
        device_id=device.id,
        device_uuid=device.device_uuid,
        payload=DeviceHeartbeatRequest(),
    )

    assert (
        device.status
        == DEVICE_STATUS_ACTIVE
    )

    assert (
        response.status
        == DEVICE_STATUS_ACTIVE
    )


@pytest.mark.asyncio
async def test_heartbeat_syncs_agent_metadata() -> None:
    device = make_device()

    session = make_session(
        device
    )

    service = DeviceHeartbeatService(
        session
    )

    await service.record_heartbeat(
        device_id=device.id,
        device_uuid=device.device_uuid,
        payload=DeviceHeartbeatRequest(
            hostname="NEW-HOSTNAME",
            agent_version="0.2.0",
        ),
    )

    assert (
        device.hostname
        == "NEW-HOSTNAME"
    )

    assert (
        device.agent_version
        == "0.2.0"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "device_status",
    [
        DEVICE_STATUS_DISABLED,
        DEVICE_STATUS_REVOKED,
    ],
)
async def test_heartbeat_rejects_forbidden_status(
    device_status: str,
) -> None:
    device = make_device(
        status=device_status
    )

    session = make_session(
        device
    )

    service = DeviceHeartbeatService(
        session
    )

    with pytest.raises(
        Exception
    ):
        await service.record_heartbeat(
            device_id=device.id,
            device_uuid=device.device_uuid,
            payload=DeviceHeartbeatRequest(),
        )

    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_heartbeat_rejects_inactive_device() -> None:
    device = make_device(
        is_active=False
    )

    session = make_session(
        device
    )

    service = DeviceHeartbeatService(
        session
    )

    with pytest.raises(
        Exception
    ):
        await service.record_heartbeat(
            device_id=device.id,
            device_uuid=device.device_uuid,
            payload=DeviceHeartbeatRequest(),
        )

    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_heartbeat_rolls_back_on_commit_failure() -> None:
    device = make_device()

    session = make_session(
        device
    )

    session.commit.side_effect = RuntimeError(
        "commit failed"
    )

    service = DeviceHeartbeatService(
        session
    )

    with pytest.raises(
        RuntimeError,
        match="commit failed",
    ):
        await service.record_heartbeat(
            device_id=device.id,
            device_uuid=device.device_uuid,
            payload=DeviceHeartbeatRequest(),
        )

    session.rollback.assert_awaited_once()