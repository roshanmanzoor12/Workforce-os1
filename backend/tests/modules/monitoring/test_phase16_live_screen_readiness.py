from __future__ import annotations

from datetime import (
    datetime,
    timedelta,
    timezone,
)
from types import SimpleNamespace
import uuid

import pytest

from app.core.exceptions import (
    ValidationError,
)
from app.modules.live_monitoring.live_screen_readiness import (
    require_live_screen_ready,
)


NOW = datetime(
    2026,
    9,
    30,
    0,
    0,
    tzinfo=timezone.utc,
)


def _device(
    *,
    last_seen_at=None,
    consent_at=None,
    capabilities=None,
    is_disabled=False,
    agent_version="1.0.0",
):
    return SimpleNamespace(
        id=uuid.uuid4(),

        employee_id=(
            uuid.uuid4()
        ),

        agent_version=(
            agent_version
        ),

        last_seen_at=(
            last_seen_at
            if last_seen_at
            is not None
            else NOW
        ),

        is_disabled=(
            is_disabled
        ),

        consent_at=(
            consent_at
            if consent_at
            is not None
            else NOW
        ),

        capabilities=(
            capabilities
            if capabilities
            is not None
            else {
                "activity_state": True,
                "live_screen": True,
            }
        ),
    )


def test_live_ready_device_is_allowed():
    require_live_screen_ready(
        device=_device(),
        now=NOW,
    )


def test_stale_agent_is_rejected():
    device = _device(
        last_seen_at=(
            NOW
            - timedelta(
                minutes=10
            )
        )
    )

    with pytest.raises(
        ValidationError,
        match="offline or stale",
    ):
        require_live_screen_ready(
            device=device,
            now=NOW,
        )


def test_missing_screen_capability_is_rejected():
    device = _device(
        capabilities={
            "activity_state": True,
        }
    )

    with pytest.raises(
        ValidationError,
        match=(
            "screen_capability_missing"
        ),
    ):
        require_live_screen_ready(
            device=device,
            now=NOW,
        )


def test_missing_consent_is_rejected():
    device = _device()

    device.consent_at = None

    with pytest.raises(
        ValidationError,
        match="consent_missing",
    ):
        require_live_screen_ready(
            device=device,
            now=NOW,
        )


def test_disabled_device_is_rejected():
    device = _device(
        is_disabled=True
    )

    with pytest.raises(
        ValidationError,
        match="device is disabled",
    ):
        require_live_screen_ready(
            device=device,
            now=NOW,
        )