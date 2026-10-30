from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .enums import (
    BillingProvider,
    SubscriptionStatus,
)
from .plans import PlanCode


@dataclass(
    frozen=True,
    slots=True,
)
class VerifiedSubscriptionState:
    user_id: str

    provider: BillingProvider
    provider_subscription_id: str

    plan_code: PlanCode
    status: SubscriptionStatus

    current_period_start: datetime | None
    current_period_end: datetime | None


def normalize_provider_subscription_id(
    value: str,
) -> str:
    normalized = value.strip()

    if not normalized:
        raise ValueError(
            "provider_subscription_id is required."
        )

    if len(normalized) > 255:
        raise ValueError(
            "provider_subscription_id is too long."
        )

    return normalized


__all__ = [
    "VerifiedSubscriptionState",
    "normalize_provider_subscription_id",
]