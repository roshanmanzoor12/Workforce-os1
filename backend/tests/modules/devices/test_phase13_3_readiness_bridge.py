from __future__ import annotations

from datetime import (
    datetime,
    timezone,
)

from app.modules.devices.readiness_policy import (
    evaluate_device_readiness,
)


NOW = datetime(
    2026,
    9,
    29,
    12,
    0,
    0,
    tzinfo=timezone.utc,
)


def test_activity_capability_can_enable_monitoring_readiness():
    decision = (
        evaluate_device_readiness(
            employee_id="employee",
            agent_version="1.0.0",
            last_seen_at=NOW,
            is_disabled=False,
            consent_at=NOW,
            capabilities={
                "activity_state": True,
            },
            now=NOW,
        )
    )

    assert (
        decision.monitoring_ready
        is True
    )


def test_activity_without_screen_is_not_live_ready():
    decision = (
        evaluate_device_readiness(
            employee_id="employee",
            agent_version="1.0.0",
            last_seen_at=NOW,
            is_disabled=False,
            consent_at=NOW,
            capabilities={
                "activity_state": True,
            },
            now=NOW,
        )
    )

    assert (
        decision.live_ready
        is False
    )


def test_activity_and_screen_capability_enable_live_ready():
    decision = (
        evaluate_device_readiness(
            employee_id="employee",
            agent_version="1.0.0",
            last_seen_at=NOW,
            is_disabled=False,
            consent_at=NOW,
            capabilities={
                "activity_state": True,
                "live_screen": True,
            },
            now=NOW,
        )
    )

    assert (
        decision.monitoring_ready
        is True
    )

    assert (
        decision.live_ready
        is True
    )