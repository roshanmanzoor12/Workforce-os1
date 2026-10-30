from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from .entitlements import AccountEntitlements
from .enums import SubscriptionStatus
from .plans import PlanCode
from .payment_policy import effective_status
from .exemptions import is_billing_exempt
from .repository import BillingRepository
from .service import BillingEntitlementService


WorkspaceCountLoader = Callable[
    [
        AsyncSession,
        uuid.UUID,
    ],
    Awaitable[int],
]


class AccountBillingService:
    def __init__(
        self,
        *,
        repository: BillingRepository | None = None,
        entitlement_service: BillingEntitlementService | None = None,
    ) -> None:
        self._repository = (
            repository
            or BillingRepository()
        )

        self._entitlement_service = (
            entitlement_service
            or BillingEntitlementService()
        )

    async def get_effective_subscription(
        self,
        session: AsyncSession,
        *,
        user_id: uuid.UUID,
    ) -> tuple[
        PlanCode,
        SubscriptionStatus,
    ]:
        if await is_billing_exempt(session, user_id):
            return PlanCode.BUSINESS, SubscriptionStatus.ACTIVE

        subscription = (
            await self._repository
            .get_subscription_for_user(
                session,
                user_id=user_id,
            )
        )

        if subscription is None:
            return (
                PlanCode.FREE,
                SubscriptionStatus.NONE,
            )

        return (
            subscription.plan_code,
            SubscriptionStatus(effective_status(
                subscription.status,
                subscription.current_period_end,
            )),
        )

    async def get_entitlements(
        self,
        session: AsyncSession,
        *,
        user_id: uuid.UUID,
        workspace_count_loader: WorkspaceCountLoader,
    ) -> AccountEntitlements:
        (
            plan_code,
            subscription_status,
        ) = await self.get_effective_subscription(
            session,
            user_id=user_id,
        )

        workspace_count = (
            await workspace_count_loader(
                session,
                user_id,
            )
        )

        if await is_billing_exempt(session, user_id):
            return AccountEntitlements(
                plan_code=PlanCode.BUSINESS,
                subscription_status=SubscriptionStatus.ACTIVE,
                workspace_limit=None, workspace_count=workspace_count,
                create_workspace=True, monitoring=True, live_screen=True,
                advanced_analytics=True,
            )

        return (
            self._entitlement_service
            .evaluate(
                plan_code=plan_code,
                subscription_status=subscription_status,
                workspace_count=workspace_count,
            )
        )
