from __future__ import annotations

from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from .enums import SubscriptionStatus
from .plans import PlanCode


class BillingPlanPublic(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    code: PlanCode
    display_name: str

    workspace_limit: int = Field(
        ge=0
    )

    member_limit_per_workspace: int = Field(
        ge=0
    )

    monitoring_enabled: bool
    live_screen_enabled: bool
    advanced_analytics_enabled: bool


class BillingPlansResponse(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    plans: list[BillingPlanPublic]


class CurrentSubscriptionPublic(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    plan_code: PlanCode
    status: SubscriptionStatus

    current_period_start: datetime | None = None
    current_period_end: datetime | None = None


class AccountEntitlementsPublic(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    plan_code: PlanCode
    subscription_status: SubscriptionStatus

    workspace_limit: int | None = Field(
        ge=0
    )

    workspace_count: int = Field(
        ge=0
    )

    create_workspace: bool
    monitoring: bool
    live_screen: bool
    advanced_analytics: bool
