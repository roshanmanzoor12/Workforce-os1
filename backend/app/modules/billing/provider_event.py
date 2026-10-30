from __future__ import annotations

import uuid
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
class VerifiedBillingProviderEvent:
    event_id: str

    user_id: uuid.UUID

    provider: BillingProvider

    provider_customer_id: str

    provider_subscription_id: str

    plan_code: PlanCode

    subscription_status: SubscriptionStatus

    current_period_start: datetime | None = None

    current_period_end: datetime | None = None


def normalize_provider_event_id(
    value: str,
) -> str:
    normalized = value.strip()

    if not normalized:
        raise ValueError(
            "provider event ID is required."
        )

    if len(normalized) > 255:
        raise ValueError(
            "provider event ID is too long."
        )

    return normalized


__all__ = [
    "VerifiedBillingProviderEvent",
    "normalize_provider_event_id",
]