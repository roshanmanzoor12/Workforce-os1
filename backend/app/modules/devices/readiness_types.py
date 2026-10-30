from __future__ import annotations

from dataclasses import dataclass
from datetime import (
    datetime,
    timezone,
)
from typing import Literal


# =========================================================
# READINESS STATES
# =========================================================


DeviceReadinessStatus = Literal[
    "online",
    "offline",
    "disabled",
]


# =========================================================
# HEARTBEAT POLICY
# =========================================================

# Existing authenticated device heartbeat cadence is 30 seconds.
#
# Readiness permits three missed heartbeat windows before a device
# is considered offline.
#
# This is intentionally derived server-side rather than trusting a
# client-supplied online/offline flag.

DEVICE_READINESS_HEARTBEAT_INTERVAL_SECONDS = 30

DEVICE_READINESS_MISSED_HEARTBEATS = 3

DEVICE_READINESS_ONLINE_TIMEOUT_SECONDS = (
    DEVICE_READINESS_HEARTBEAT_INTERVAL_SECONDS
    * DEVICE_READINESS_MISSED_HEARTBEATS
)


# =========================================================
# SETUP REASONS
# =========================================================


REASON_DEVICE_DISABLED = (
    "device_disabled"
)

REASON_EMPLOYEE_NOT_ASSIGNED = (
    "employee_not_assigned"
)

REASON_AGENT_VERSION_MISSING = (
    "agent_version_missing"
)

REASON_CONSENT_MISSING = (
    "consent_missing"
)

REASON_ACTIVITY_CAPABILITY_MISSING = (
    "activity_capability_missing"
)

REASON_SCREEN_CAPABILITY_MISSING = (
    "screen_capability_missing"
)


# =========================================================
# INTERNAL POLICY RESULT
# =========================================================


@dataclass(
    frozen=True,
    slots=True,
)
class DeviceReadinessDecision:
    status: DeviceReadinessStatus

    is_online: bool

    monitoring_ready: bool

    live_ready: bool

    needs_setup: bool

    setup_reasons: tuple[
        str,
        ...,
    ]

    heartbeat_age_seconds: (
        int
        | None
    )


# =========================================================
# TIME
# =========================================================


def utc_now() -> datetime:
    return datetime.now(
        timezone.utc
    )


__all__ = [
    "DeviceReadinessStatus",
    "DEVICE_READINESS_HEARTBEAT_INTERVAL_SECONDS",
    "DEVICE_READINESS_MISSED_HEARTBEATS",
    "DEVICE_READINESS_ONLINE_TIMEOUT_SECONDS",
    "REASON_DEVICE_DISABLED",
    "REASON_EMPLOYEE_NOT_ASSIGNED",
    "REASON_AGENT_VERSION_MISSING",
    "REASON_CONSENT_MISSING",
    "REASON_ACTIVITY_CAPABILITY_MISSING",
    "REASON_SCREEN_CAPABILITY_MISSING",
    "DeviceReadinessDecision",
    "utc_now",
]