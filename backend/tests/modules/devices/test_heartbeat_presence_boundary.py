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
)


def make_device(
    *,
    last_seen_at: datetime | None,
) -> SimpleNamespace:
    return SimpleNamespace(
        status=DEVICE_STATUS_ACTIVE,
        is_active=True,
        last_seen_at=last_seen_at,
    )


@pytest.mark.parametrize(
    (
        "age_seconds",
        "expected_online",
    ),
    [
        (
            0,
            True,
        ),
        (
            30,
            True,
        ),
        (
            60,
            True,
        ),
        (
            DEVICE_ONLINE_TIMEOUT_SECONDS
            - 1,
            True,
        ),
        (
            DEVICE_ONLINE_TIMEOUT_SECONDS,
            True,
        ),
        (
            DEVICE_ONLINE_TIMEOUT_SECONDS
            + 1,
            False,
        ),
        (
            DEVICE_ONLINE_TIMEOUT_SECONDS
            + 60,
            False,
        ),
    ],
)
def test_presence_timeout_boundaries(
    age_seconds: int,
    expected_online: bool,
) -> None:
    now = datetime.now(
        timezone.utc
    )

    last_seen_at = (
        now
        - timedelta(
            seconds=age_seconds
        )
    )

    device = make_device(
        last_seen_at=last_seen_at
    )

    presence = get_device_presence(
        device,
        now=now,
    )

    assert (
        presence.is_online
        is expected_online
    )

    if expected_online:
        assert (
            presence.offline_since
            is None
        )

    else:
        assert (
            presence.offline_since
            == (
                last_seen_at
                + timedelta(
                    seconds=(
                        DEVICE_ONLINE_TIMEOUT_SECONDS
                    )
                )
            )
        )