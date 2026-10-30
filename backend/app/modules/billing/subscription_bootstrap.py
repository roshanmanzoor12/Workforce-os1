from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from .models import BillingSubscription
from .repository import BillingRepository


class SubscriptionBootstrapService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        repository: BillingRepository | None = None,
    ) -> None:
        self.session = session

        self.repository = (
            repository
            or BillingRepository()
        )

    async def ensure_for_user(
        self,
        *,
        user_id: uuid.UUID,
    ) -> BillingSubscription:
        subscription = (
            await self.repository
            .ensure_subscription(
                self.session,
                user_id=user_id,
            )
        )

        return subscription


__all__ = [
    "SubscriptionBootstrapService",
]