from __future__ import annotations

from datetime import (
    datetime,
    timezone,
)
from typing import Mapping

from app.modules.devices.readiness_types import (
    DEVICE_READINESS_ONLINE_TIMEOUT_SECONDS,
    REASON_ACTIVITY_CAPABILITY_MISSING,
    REASON_AGENT_VERSION_MISSING,
    REASON_CONSENT_MISSING,
    REASON_DEVICE_DISABLED,
    REASON_EMPLOYEE_NOT_ASSIGNED,
    REASON_SCREEN_CAPABILITY_MISSING,
    DeviceReadinessDecision,
)


# =========================================================
# CAPABILITY KEYS
# =========================================================

# Existing agent capabilities currently contain heartbeat and
# explicit privacy-safe capture capability flags.
#
# Future agent releases may use one of these names for activity
# observation. Supporting aliases keeps readiness backward-safe
# without claiming capability when none is present.

ACTIVITY_CAPABILITY_KEYS = (
    "activity_state",
    "activity_reporting",
    "activity_capture",
)

SCREEN_CAPABILITY_KEYS = (
    "live_screen",
    "screen_capture",
    "screenshot_capture",
)


# =========================================================
# HELPERS
# =========================================================


def _normalize_datetime(
    value: datetime,
) -> datetime:
    if value.tzinfo is None:
        return value.replace(
            tzinfo=timezone.utc
        )

    return value.astimezone(
        timezone.utc
    )


def _capability_enabled(
    capabilities: Mapping[
        str,
        object,
    ],
    keys: tuple[
        str,
        ...,
    ],
) -> bool:
    for key in keys:
        value = capabilities.get(
            key
        )

        if value is True:
            return True

    return False


def heartbeat_age_seconds(
    *,
    last_seen_at: datetime | None,
    now: datetime,
) -> int | None:
    if last_seen_at is None:
        return None

    normalized_seen = (
        _normalize_datetime(
            last_seen_at
        )
    )

    normalized_now = (
        _normalize_datetime(
            now
        )
    )

    seconds = int(
        (
            normalized_now
            - normalized_seen
        ).total_seconds()
    )

    # Clock drift must never produce a negative age.
    return max(
        seconds,
        0,
    )


# =========================================================
# POLICY
# =========================================================


def evaluate_device_readiness(
    *,
    employee_id,
    agent_version: str | None,
    last_seen_at: datetime | None,
    is_disabled: bool,
    consent_at: datetime | None,
    capabilities: Mapping[
        str,
        object,
    ] | None,
    now: datetime,
    online_timeout_seconds: int = (
        DEVICE_READINESS_ONLINE_TIMEOUT_SECONDS
    ),
) -> DeviceReadinessDecision:
    """
    Derive operational readiness from persisted evidence.

    Important:

    - browser/client does not decide online state;
    - stale heartbeat means offline;
    - missing capabilities remain false;
    - readiness never invents screen/activity permission;
    - disabled devices are never online/ready.
    """

    if online_timeout_seconds <= 0:
        raise ValueError(
            "online_timeout_seconds must "
            "be greater than zero."
        )

    capability_map = dict(
        capabilities
        or {}
    )

    age = heartbeat_age_seconds(
        last_seen_at=last_seen_at,
        now=now,
    )

    heartbeat_fresh = (
        age is not None
        and age
        <= online_timeout_seconds
    )

    is_online = (
        not is_disabled
        and heartbeat_fresh
    )

    activity_capability = (
        _capability_enabled(
            capability_map,
            ACTIVITY_CAPABILITY_KEYS,
        )
    )

    screen_capability = (
        _capability_enabled(
            capability_map,
            SCREEN_CAPABILITY_KEYS,
        )
    )

    consent_granted = (
        consent_at is not None
    )

    has_employee = (
        employee_id is not None
    )

    has_agent_version = bool(
        (
            agent_version
            or ""
        ).strip()
    )

    monitoring_ready = (
        is_online
        and has_employee
        and has_agent_version
        and consent_granted
        and activity_capability
    )

    live_ready = (
        monitoring_ready
        and screen_capability
    )

    reasons: list[str] = []

    if is_disabled:
        reasons.append(
            REASON_DEVICE_DISABLED
        )

    if not has_employee:
        reasons.append(
            REASON_EMPLOYEE_NOT_ASSIGNED
        )

    if not has_agent_version:
        reasons.append(
            REASON_AGENT_VERSION_MISSING
        )

    if not consent_granted:
        reasons.append(
            REASON_CONSENT_MISSING
        )

    if not activity_capability:
        reasons.append(
            REASON_ACTIVITY_CAPABILITY_MISSING
        )

    if not screen_capability:
        reasons.append(
            REASON_SCREEN_CAPABILITY_MISSING
        )

    # Offline is an operational state and by itself does not mean
    # the agent needs configuration. Needs Setup is reserved for
    # missing assignment/consent/capability/configuration evidence.

    needs_setup = bool(
        reasons
    )

    if is_disabled:
        status = "disabled"

    elif is_online:
        status = "online"

    else:
        status = "offline"

    return DeviceReadinessDecision(
        status=status,
        is_online=is_online,
        monitoring_ready=(
            monitoring_ready
        ),
        live_ready=live_ready,
        needs_setup=needs_setup,
        setup_reasons=tuple(
            reasons
        ),
        heartbeat_age_seconds=age,
    )


__all__ = [
    "ACTIVITY_CAPABILITY_KEYS",
    "SCREEN_CAPABILITY_KEYS",
    "heartbeat_age_seconds",
    "evaluate_device_readiness",
]