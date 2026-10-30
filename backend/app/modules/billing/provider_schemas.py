from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from .enums import (
    BillingProvider,
    SubscriptionStatus,
)
from .plans import PlanCode


class VerifiedProviderSubscriptionInput(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid",
    )

    user_id: uuid.UUID

    provider: BillingProvider

    provider_subscription_id: str = Field(
        min_length=1,
        max_length=255,
    )

    plan_code: PlanCode

    status: SubscriptionStatus

    current_period_start: datetime | None = None

    current_period_end: datetime | None = None


class ProviderSubscriptionApplyResult(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid",
    )

    user_id: uuid.UUID

    plan_code: PlanCode

    status: SubscriptionStatus

    applied: bool