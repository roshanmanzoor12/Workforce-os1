from __future__ import annotations

from dataclasses import dataclass

from .enums import SubscriptionStatus
from .plans import (
    PlanCode,
    PlanDefinition,
    get_plan_definition,
)


ACTIVE_BILLING_STATES = {
    SubscriptionStatus.TRIALING,
    SubscriptionStatus.ACTIVE,
}


@dataclass(frozen=True, slots=True)
class AccountEntitlements:
    plan_code: PlanCode
    subscription_status: SubscriptionStatus

    workspace_limit: int | None
    workspace_count: int

    create_workspace: bool
    monitoring: bool
    live_screen: bool
    advanced_analytics: bool


def evaluate_account_entitlements(
    *,
    plan_code: PlanCode,
    subscription_status: SubscriptionStatus,
    workspace_count: int,
) -> AccountEntitlements:
    if workspace_count < 0:
        raise ValueError(
            "workspace_count cannot be negative"
        )

    plan: PlanDefinition = get_plan_definition(
        plan_code
    )

    billing_active = (
        subscription_status
        in ACTIVE_BILLING_STATES
    )

    if plan_code == PlanCode.FREE:
        billing_active = True

    create_workspace = (
        billing_active
        and plan.workspace_limit > 0
        and workspace_count < plan.workspace_limit
    )

    return AccountEntitlements(
        plan_code=plan_code,
        subscription_status=subscription_status,
        workspace_limit=plan.workspace_limit,
        workspace_count=workspace_count,
        create_workspace=create_workspace,
        monitoring=(
            billing_active
            and plan.monitoring_enabled
        ),
        live_screen=(
            billing_active
            and plan.live_screen_enabled
        ),
        advanced_analytics=(
            billing_active
            and plan.advanced_analytics_enabled
        ),
    )
