from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from .customer_service import (
    BillingCustomerService,
)
from .enums import BillingProvider
from .provider_event import (
    VerifiedBillingProviderEvent,
    normalize_provider_event_id,
)
from .provider_schemas import (
    ProviderSubscriptionApplyResult,
    VerifiedProviderSubscriptionInput,
)
from .provider_service import (
    BillingProviderStateService,
)


class BillingProviderEventService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        customer_service: BillingCustomerService | None = None,
        state_service: BillingProviderStateService | None = None,
    ) -> None:
        self.session = session

        self.customer_service = (
            customer_service
            or BillingCustomerService(
                session
            )
        )

        self.state_service = (
            state_service
            or BillingProviderStateService(
                session
            )
        )

    async def apply_verified_event(
        self,
        event: VerifiedBillingProviderEvent,
    ) -> ProviderSubscriptionApplyResult:
        normalize_provider_event_id(
            event.event_id
        )

        if (
            event.provider
            == BillingProvider.NONE
        ):
            raise ValueError(
                "Verified provider event cannot "
                "use BillingProvider.NONE."
            )

        await self.customer_service.apply_provider_customer(
            user_id=event.user_id,
            provider=event.provider,
            provider_customer_id=(
                event.provider_customer_id
            ),
        )

        result = (
            await self.state_service
            .apply_verified_state(
                VerifiedProviderSubscriptionInput(
                    user_id=event.user_id,
                    provider=event.provider,
                    provider_subscription_id=(
                        event.provider_subscription_id
                    ),
                    plan_code=(
                        event.plan_code
                    ),
                    status=(
                        event.subscription_status
                    ),
                    current_period_start=(
                        event.current_period_start
                    ),
                    current_period_end=(
                        event.current_period_end
                    ),
                )
            )
        )

        return result


__all__ = [
    "BillingProviderEventService",
]