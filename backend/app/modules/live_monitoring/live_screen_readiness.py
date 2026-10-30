from __future__ import annotations

from datetime import (
    datetime,
    timezone,
)
from typing import Any

from app.core.exceptions import (
    ValidationError,
)
from app.modules.devices.readiness_policy import (
    evaluate_device_readiness,
)


# =========================================================
# TIME
# =========================================================


def utc_now() -> datetime:
    return datetime.now(
        timezone.utc
    )


# =========================================================
# LIVE SCREEN READINESS
# =========================================================


def require_live_screen_ready(
    *,
    device: Any,
    now: datetime | None = None,
) -> None:
    """
    Require backend-authoritative Live Screen readiness.

    The browser must never decide whether a device is online
    or capture-capable.

    Reuses the canonical Phase 13.2 readiness policy so
    Monitoring Overview, Employee Monitoring Detail and
    Live Screens cannot drift into different readiness rules.
    """

    resolved_now = (
        now
        if now is not None
        else utc_now()
    )

    decision = evaluate_device_readiness(
        employee_id=getattr(
            device,
            "employee_id",
            None,
        ),

        agent_version=getattr(
            device,
            "agent_version",
            None,
        ),

        last_seen_at=getattr(
            device,
            "last_seen_at",
            None,
        ),

        is_disabled=bool(
            getattr(
                device,
                "is_disabled",
                False,
            )
        ),

        consent_at=getattr(
            device,
            "consent_at",
            None,
        ),

        capabilities=(
            getattr(
                device,
                "capabilities",
                None,
            )
            or {}
        ),

        now=resolved_now,
    )

    if decision.status == "disabled":
        raise ValidationError(
            "Live screen unavailable: "
            "device is disabled."
        )

    if not decision.is_online:
        raise ValidationError(
            "Live screen unavailable: "
            "agent is offline or stale."
        )

    if not decision.live_ready:
        reasons = (
            ", ".join(
                decision.setup_reasons
            )
            or "device_not_live_ready"
        )

        raise ValidationError(
            "Live screen unavailable: "
            f"{reasons}."
        )


__all__ = [
    "require_live_screen_ready",
    "utc_now",
]