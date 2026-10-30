from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from .enums import (
    BillingProvider,
    SubscriptionStatus,
)
from .models import BillingSubscription
from .plans import PlanCode
from .repository import BillingRepository


class SubscriptionService:
    def __init__(
        self,
        *,
        repository: BillingRepository | None = None,
    ) -> None:
        self._repository = (
            repository
            or BillingRepository()
        )

    async def ensure_default_subscription(
        self,
        session: AsyncSession,
        *,
        user_id: uuid.UUID,
    ) -> BillingSubscription:
        return await self._repository.ensure_subscription(
            session,
            user_id=user_id,
        )

    async def apply_provider_state(
        self,
        session: AsyncSession,
        *,
        user_id: uuid.UUID,
        provider: BillingProvider,
        provider_subscription_id: str,
        plan_code: PlanCode,
        status: SubscriptionStatus,
        current_period_start: datetime | None,
        current_period_end: datetime | None,
    ) -> BillingSubscription:
        if provider == BillingProvider.NONE:
            raise ValueError(
                "A provider subscription cannot use "
                "BillingProvider.NONE."
            )

        provider_subscription_id = (
            provider_subscription_id.strip()
        )

        if not provider_subscription_id:
            raise ValueError(
                "provider_subscription_id is required."
            )

        subscription = (
            await self._repository
            .ensure_subscription(
                session,
                user_id=user_id,
            )
        )

        subscription.plan_code = (
            plan_code
        )

        subscription.provider = (
            provider
        )

        subscription.provider_subscription_id = (
            provider_subscription_id
        )

        subscription.status = (
            status
        )

        subscription.current_period_start = (
            current_period_start
        )

        subscription.current_period_end = (
            current_period_end
        )

        await session.flush()

        return subscription

    async def cancel_subscription(
        self,
        session: AsyncSession,
        *,
        user_id: uuid.UUID,
    ) -> BillingSubscription:
        subscription = (
            await self._repository
            .ensure_subscription(
                session,
                user_id=user_id,
            )
        )

        subscription.status = (
            SubscriptionStatus.CANCELED
        )

        await session.flush()

        return subscription