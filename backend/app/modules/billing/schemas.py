from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from .enums import (
    EntitlementCode,
    SubscriptionStatus,
)
from .plans import PlanCode


class PlanResponse(BaseModel):
    code: PlanCode
    display_name: str
    workspace_limit: int
    member_limit_per_workspace: int
    monitoring_enabled: bool
    live_screen_enabled: bool
    advanced_analytics_enabled: bool


class SubscriptionResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    plan_code: PlanCode
    status: SubscriptionStatus
    current_period_start: datetime | None
    current_period_end: datetime | None


class EntitlementResponse(BaseModel):
    entitlement: EntitlementCode
    allowed: bool
    reason: str | None = None


class AccountEntitlementsResponse(BaseModel):
    plan_code: PlanCode
    subscription_status: SubscriptionStatus
    workspace_limit: int | None
    workspace_count: int

    create_workspace: bool
    monitoring: bool
    live_screen: bool
    advanced_analytics: bool
