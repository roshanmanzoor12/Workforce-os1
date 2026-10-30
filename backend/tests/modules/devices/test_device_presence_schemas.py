from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

from app.modules.devices.heartbeat_presence_schemas import (
    DevicePresenceResponse,
)


def test_presence_response_accepts_online_device() -> None:
    device_uuid = uuid.uuid4()

    now = datetime.now(
        timezone.utc
    )

    response = DevicePresenceResponse(
        device_uuid=device_uuid,
        is_online=True,
        last_seen_at=now,
        offline_since=None,
        online_timeout_seconds=90,
    )

    assert response.device_uuid == device_uuid

    assert response.is_online is True

    assert response.last_seen_at == now

    assert response.offline_since is None

    assert (
        response.online_timeout_seconds
        == 90
    )


def test_presence_response_accepts_offline_device() -> None:
    device_uuid = uuid.uuid4()

    last_seen_at = datetime.now(
        timezone.utc
    )

    response = DevicePresenceResponse(
        device_uuid=device_uuid,
        is_online=False,
        last_seen_at=last_seen_at,
        offline_since=last_seen_at,
        online_timeout_seconds=90,
    )

    assert response.device_uuid == device_uuid

    assert response.is_online is False

    assert response.last_seen_at == last_seen_at

    assert (
        response.offline_since
        == last_seen_at
    )


def test_presence_response_supports_from_attributes() -> None:
    device_uuid = uuid.uuid4()

    source = SimpleNamespace(
        device_uuid=device_uuid,
        is_online=True,
        last_seen_at=datetime.now(
            timezone.utc
        ),
        offline_since=None,
        online_timeout_seconds=90,
    )

    response = (
        DevicePresenceResponse
        .model_validate(
            source
        )
    )

    assert (
        response.device_uuid
        == device_uuid
    )

    assert response.is_online is True

    assert response.last_seen_at is not None

    assert response.offline_since is None


def test_presence_response_supports_never_seen_device() -> None:
    response = DevicePresenceResponse(
        device_uuid=uuid.uuid4(),
        is_online=False,
        last_seen_at=None,
        offline_since=None,
        online_timeout_seconds=90,
    )

    assert response.is_online is False

    assert response.last_seen_at is None

    assert response.offline_since is None

    assert (
        response.online_timeout_seconds
        == 90
    )