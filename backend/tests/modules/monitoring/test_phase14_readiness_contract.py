from __future__ import annotations

from app.modules.devices.readiness_schemas import (
    DeviceReadinessItem,
    DeviceReadinessSummary,
)


def test_readiness_row_contains_monitoring_evidence():
    fields = set(
        DeviceReadinessItem
        .model_fields
        .keys()
    )

    required = {
        "device_id",
        "employee_id",
        "status",
        "last_seen_at",
        "heartbeat_age_seconds",
        "is_online",
        "activity_capability",
        "screen_capability",
        "monitoring_ready",
        "live_ready",
        "needs_setup",
        "setup_reasons",
    }

    assert required.issubset(
        fields
    )


def test_readiness_summary_supports_overview_cards():
    fields = set(
        DeviceReadinessSummary
        .model_fields
        .keys()
    )

    required = {
        "total",
        "online",
        "offline",
        "monitoring_ready",
        "live_ready",
        "needs_setup",
        "online_timeout_seconds",
    }

    assert required.issubset(
        fields
    )