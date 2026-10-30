from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from .account_service import (
    AccountBillingService,
)
from .enums import SubscriptionStatus
from .plans import PlanCode
from .workspace_count import (
    count_owned_active_workspaces,
)


@dataclass(
    frozen=True,
    slots=True,
)
class BillingAccountSnapshot:
    user_id: uuid.UUID

    plan_code: PlanCode

    subscription_status: SubscriptionStatus

    workspace_limit: int | None

    workspace_count: int

    can_create_workspace: bool

    monitoring_enabled: bool

    live_screen_enabled: bool

    advanced_analytics_enabled: bool


class BillingSnapshotService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        account_service: AccountBillingService | None = None,
    ) -> None:
        self.session = session

        self.account_service = (
            account_service
            or AccountBillingService()
        )

    async def get_snapshot(
        self,
        *,
        user_id: uuid.UUID,
    ) -> BillingAccountSnapshot:
        entitlements = (
            await self.account_service
            .get_entitlements(
                self.session,
                user_id=user_id,
                workspace_count_loader=(
                    count_owned_active_workspaces
                ),
            )
        )

        return BillingAccountSnapshot(
            user_id=user_id,
            plan_code=(
                entitlements.plan_code
            ),
            subscription_status=(
                entitlements.subscription_status
            ),
            workspace_limit=(
                entitlements.workspace_limit
            ),
            workspace_count=(
                entitlements.workspace_count
            ),
            can_create_workspace=(
                entitlements.create_workspace
            ),
            monitoring_enabled=(
                entitlements.monitoring
            ),
            live_screen_enabled=(
                entitlements.live_screen
            ),
            advanced_analytics_enabled=(
                entitlements.advanced_analytics
            ),
        )


__all__ = [
    "BillingAccountSnapshot",
    "BillingSnapshotService",
]
