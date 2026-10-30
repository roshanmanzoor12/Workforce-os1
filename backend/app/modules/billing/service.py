from __future__ import annotations

from .entitlements import (
    AccountEntitlements,
    evaluate_account_entitlements,
)
from .enums import SubscriptionStatus
from .plans import PlanCode


class BillingEntitlementService:
    def evaluate(
        self,
        *,
        plan_code: PlanCode,
        subscription_status: SubscriptionStatus,
        workspace_count: int,
    ) -> AccountEntitlements:
        return evaluate_account_entitlements(
            plan_code=plan_code,
            subscription_status=subscription_status,
            workspace_count=workspace_count,
        )

    def require_workspace_creation(
        self,
        *,
        plan_code: PlanCode,
        subscription_status: SubscriptionStatus,
        workspace_count: int,
    ) -> AccountEntitlements:
        entitlements = self.evaluate(
            plan_code=plan_code,
            subscription_status=subscription_status,
            workspace_count=workspace_count,
        )

        if not entitlements.create_workspace:
            from .exceptions import (
                WorkspaceEntitlementDeniedError,
            )

            raise WorkspaceEntitlementDeniedError(
                "Current account entitlement does not "
                "allow creation of another workspace."
            )

        return entitlements