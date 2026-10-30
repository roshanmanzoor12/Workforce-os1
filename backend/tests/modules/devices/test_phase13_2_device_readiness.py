from __future__ import annotations

from datetime import (
    datetime,
    timedelta,
    timezone,
)

from app.modules.devices.readiness_policy import (
    evaluate_device_readiness,
    heartbeat_age_seconds,
)
from app.modules.devices.readiness_schemas import (
    DeviceReadinessResponse,
    DeviceReadinessSummary,
)
from app.modules.devices.readiness_types import (
    DEVICE_READINESS_ONLINE_TIMEOUT_SECONDS,
    REASON_ACTIVITY_CAPABILITY_MISSING,
    REASON_SCREEN_CAPABILITY_MISSING,
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


def test_heartbeat_age_is_server_derived():
    seen = NOW - timedelta(
        seconds=45
    )

    assert heartbeat_age_seconds(
        last_seen_at=seen,
        now=NOW,
    ) == 45


def test_future_heartbeat_clock_drift_clamps_zero():
    seen = NOW + timedelta(
        seconds=10
    )

    assert heartbeat_age_seconds(
        last_seen_at=seen,
        now=NOW,
    ) == 0


def test_recent_heartbeat_is_online():
    decision = (
        evaluate_device_readiness(
            employee_id="employee",
            agent_version="1.0.0",
            last_seen_at=(
                NOW
                - timedelta(
                    seconds=30
                )
            ),
            is_disabled=False,
            consent_at=NOW,
            capabilities={
                "activity_state": True,
                "live_screen": True,
            },
            now=NOW,
        )
    )

    assert decision.is_online
    assert decision.status == "online"


def test_stale_heartbeat_is_offline():
    decision = (
        evaluate_device_readiness(
            employee_id="employee",
            agent_version="1.0.0",
            last_seen_at=(
                NOW
                - timedelta(
                    seconds=(
                        DEVICE_READINESS_ONLINE_TIMEOUT_SECONDS
                        + 1
                    )
                )
            ),
            is_disabled=False,
            consent_at=NOW,
            capabilities={
                "activity_state": True,
                "live_screen": True,
            },
            now=NOW,
        )
    )

    assert not decision.is_online
    assert decision.status == "offline"


def test_disabled_device_is_never_online():
    decision = (
        evaluate_device_readiness(
            employee_id="employee",
            agent_version="1.0.0",
            last_seen_at=NOW,
            is_disabled=True,
            consent_at=NOW,
            capabilities={
                "activity_state": True,
                "live_screen": True,
            },
            now=NOW,
        )
    )

    assert not decision.is_online
    assert decision.status == "disabled"
    assert decision.needs_setup


def test_monitoring_ready_requires_activity_capability():
    decision = (
        evaluate_device_readiness(
            employee_id="employee",
            agent_version="1.0.0",
            last_seen_at=NOW,
            is_disabled=False,
            consent_at=NOW,
            capabilities={
                "live_screen": True,
            },
            now=NOW,
        )
    )

    assert not decision.monitoring_ready

    assert (
        REASON_ACTIVITY_CAPABILITY_MISSING
        in decision.setup_reasons
    )


def test_live_ready_requires_screen_capability():
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

    assert decision.monitoring_ready

    assert not decision.live_ready

    assert (
        REASON_SCREEN_CAPABILITY_MISSING
        in decision.setup_reasons
    )


def test_full_capability_device_is_live_ready():
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

    assert decision.monitoring_ready
    assert decision.live_ready
    assert not decision.needs_setup


def test_offline_alone_does_not_mean_setup_missing():
    decision = (
        evaluate_device_readiness(
            employee_id="employee",
            agent_version="1.0.0",
            last_seen_at=(
                NOW
                - timedelta(
                    hours=1
                )
            ),
            is_disabled=False,
            consent_at=NOW,
            capabilities={
                "activity_state": True,
                "live_screen": True,
            },
            now=NOW,
        )
    )

    assert decision.status == "offline"
    assert not decision.needs_setup


def test_summary_schema_contract():
    response = DeviceReadinessResponse(
        summary=DeviceReadinessSummary(
            total=5,
            online=3,
            offline=1,
            disabled=1,
            monitoring_ready=2,
            live_ready=1,
            needs_setup=2,
            online_timeout_seconds=90,
        ),
        devices=[],
    )

    assert response.summary.total == 5
    assert response.summary.online == 3
    assert response.summary.live_ready == 1


def test_readiness_schema_has_no_secret_fields():
    fields = set(
        DeviceReadinessResponse
        .model_fields
    )

    assert "device_secret" not in fields
    assert "secret_hash" not in fields
    assert "database_name" not in fields
    assert "cluster_key" not in fields