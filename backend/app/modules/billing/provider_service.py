from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from .enums import BillingProvider
from .provider_schemas import (
    ProviderSubscriptionApplyResult,
    VerifiedProviderSubscriptionInput,
)
from .repository import BillingRepository
from .subscription_service import (
    SubscriptionService,
)


class BillingProviderStateService:
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

        self.subscription_service = (
            SubscriptionService(
                repository=self.repository
            )
        )

    async def apply_verified_state(
        self,
        request: VerifiedProviderSubscriptionInput,
    ) -> ProviderSubscriptionApplyResult:
        if (
            request.provider
            == BillingProvider.NONE
        ):
            raise ValueError(
                "Verified provider state cannot "
                "use BillingProvider.NONE."
            )

        subscription = (
            await self.subscription_service
            .apply_provider_state(
                self.session,
                user_id=request.user_id,
                provider=request.provider,
                provider_subscription_id=(
                    request.provider_subscription_id
                ),
                plan_code=request.plan_code,
                status=request.status,
                current_period_start=(
                    request.current_period_start
                ),
                current_period_end=(
                    request.current_period_end
                ),
            )
        )

        return ProviderSubscriptionApplyResult(
            user_id=request.user_id,
            plan_code=subscription.plan_code,
            status=subscription.status,
            applied=True,
        )


__all__ = [
    "BillingProviderStateService",
]