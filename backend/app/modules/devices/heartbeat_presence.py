from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.modules.devices.models import (
    DEVICE_STATUS_DISABLED,
    DEVICE_STATUS_REVOKED,
    Device,
)


__all__ = [
    "DEVICE_ONLINE_TIMEOUT_SECONDS",
    "DevicePresence",
    "get_device_presence",
]


DEVICE_ONLINE_TIMEOUT_SECONDS = 90


class DevicePresence:
    def __init__(
        self,
        *,
        is_online: bool,
        last_seen_at: datetime | None,
        offline_since: datetime | None,
    ) -> None:
        self.is_online = is_online
        self.last_seen_at = last_seen_at
        self.offline_since = offline_since


def _now() -> datetime:
    return datetime.now(
        timezone.utc
    )


def get_device_presence(
    device: Device,
    *,
    now: datetime | None = None,
) -> DevicePresence:
    """
    Derive online/offline presence from the last authenticated
    heartbeat timestamp.

    Presence is intentionally derived instead of trusting an
    agent-provided online/offline flag.
    """

    effective_now = now or _now()

    if (
        not device.is_active
        or device.status
        in {
            DEVICE_STATUS_DISABLED,
            DEVICE_STATUS_REVOKED,
        }
    ):
        return DevicePresence(
            is_online=False,
            last_seen_at=device.last_seen_at,
            offline_since=device.last_seen_at,
        )

    if device.last_seen_at is None:
        return DevicePresence(
            is_online=False,
            last_seen_at=None,
            offline_since=None,
        )

    last_seen_at = device.last_seen_at

    if last_seen_at.tzinfo is None:
        last_seen_at = last_seen_at.replace(
            tzinfo=timezone.utc
        )

    online_cutoff = (
        effective_now
        - timedelta(
            seconds=(
                DEVICE_ONLINE_TIMEOUT_SECONDS
            )
        )
    )

    is_online = (
        last_seen_at >= online_cutoff
    )

    offline_since: datetime | None = None

    if not is_online:
        offline_since = (
            last_seen_at
            + timedelta(
                seconds=(
                    DEVICE_ONLINE_TIMEOUT_SECONDS
                )
            )
        )

    return DevicePresence(
        is_online=is_online,
        last_seen_at=last_seen_at,
        offline_since=offline_since,
    )