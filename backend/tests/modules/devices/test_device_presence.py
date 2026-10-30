from __future__ import annotations

from datetime import (
    datetime,
    timedelta,
    timezone,
)
from types import SimpleNamespace

import pytest

from app.modules.devices.heartbeat_presence import (
    DEVICE_ONLINE_TIMEOUT_SECONDS,
    get_device_presence,
)
from app.modules.devices.models import (
    DEVICE_STATUS_ACTIVE,
    DEVICE_STATUS_DISABLED,
    DEVICE_STATUS_REVOKED,
)


def make_device(
    *,
    status: str = DEVICE_STATUS_ACTIVE,
    is_active: bool = True,
    last_seen_at: datetime | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        status=status,
        is_active=is_active,
        last_seen_at=last_seen_at,
    )


def test_recent_heartbeat_is_online() -> None:
    now = datetime.now(
        timezone.utc
    )

    device = make_device(
        last_seen_at=(
            now
            - timedelta(
                seconds=30
            )
        )
    )

    presence = get_device_presence(
        device,
        now=now,
    )

    assert presence.is_online is True

    assert (
        presence.offline_since
        is None
    )


def test_missing_heartbeat_is_offline() -> None:
    now = datetime.now(
        timezone.utc
    )

    device = make_device(
        last_seen_at=None
    )

    presence = get_device_presence(
        device,
        now=now,
    )

    assert presence.is_online is False

    assert (
        presence.last_seen_at
        is None
    )

    assert (
        presence.offline_since
        is None
    )


def test_stale_heartbeat_is_offline() -> None:
    now = datetime.now(
        timezone.utc
    )

    last_seen = (
        now
        - timedelta(
            seconds=(
                DEVICE_ONLINE_TIMEOUT_SECONDS
                + 10
            )
        )
    )

    device = make_device(
        last_seen_at=last_seen
    )

    presence = get_device_presence(
        device,
        now=now,
    )

    assert presence.is_online is False

    assert (
        presence.offline_since
        == (
            last_seen
            + timedelta(
                seconds=(
                    DEVICE_ONLINE_TIMEOUT_SECONDS
                )
            )
        )
    )


def test_exact_timeout_boundary_is_online() -> None:
    now = datetime.now(
        timezone.utc
    )

    last_seen = (
        now
        - timedelta(
            seconds=(
                DEVICE_ONLINE_TIMEOUT_SECONDS
            )
        )
    )

    device = make_device(
        last_seen_at=last_seen
    )

    presence = get_device_presence(
        device,
        now=now,
    )

    assert presence.is_online is True


@pytest.mark.parametrize(
    "status",
    [
        DEVICE_STATUS_DISABLED,
        DEVICE_STATUS_REVOKED,
    ],
)
def test_disabled_or_revoked_is_offline(
    status: str,
) -> None:
    now = datetime.now(
        timezone.utc
    )

    device = make_device(
        status=status,
        last_seen_at=now,
    )

    presence = get_device_presence(
        device,
        now=now,
    )

    assert presence.is_online is False


def test_inactive_device_is_offline() -> None:
    now = datetime.now(
        timezone.utc
    )

    device = make_device(
        is_active=False,
        last_seen_at=now,
    )

    presence = get_device_presence(
        device,
        now=now,
    )

    assert presence.is_online is False


def test_naive_timestamp_is_treated_as_utc() -> None:
    now = datetime.now(
        timezone.utc
    )

    naive_last_seen = (
        now
        - timedelta(
            seconds=10
        )
    ).replace(
        tzinfo=None
    )

    device = make_device(
        last_seen_at=naive_last_seen
    )

    presence = get_device_presence(
        device,
        now=now,
    )

    assert presence.is_online is True

    assert (
        presence.last_seen_at
        is not None
    )

    assert (
        presence.last_seen_at.tzinfo
        is not None
    )