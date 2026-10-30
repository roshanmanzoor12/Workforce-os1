from __future__ import annotations

import uuid

import pytest

from app.modules.billing.enums import (
    BillingProvider,
    SubscriptionStatus,
)
from app.modules.billing.plans import (
    PlanCode,
)
from app.modules.billing.provider_schemas import (
    VerifiedProviderSubscriptionInput,
)
from app.modules.billing.provider_service import (
    BillingProviderStateService,
)


class FakeSubscription:
    def __init__(
        self,
    ) -> None:
        self.plan_code = (
            PlanCode.STARTER
        )

        self.status = (
            SubscriptionStatus.ACTIVE
        )


class FakeSubscriptionService:
    async def apply_provider_state(
        self,
        session,
        **kwargs,
    ):
        return FakeSubscription()


@pytest.mark.asyncio
async def test_verified_state_is_applied():
    service = BillingProviderStateService(
        None
    )

    service.subscription_service = (
        FakeSubscriptionService()
    )

    user_id = uuid.uuid4()

    result = await service.apply_verified_state(
        VerifiedProviderSubscriptionInput(
            user_id=user_id,
            provider=BillingProvider.STRIPE,
            provider_subscription_id="sub_test",
            plan_code=PlanCode.STARTER,
            status=SubscriptionStatus.ACTIVE,
        )
    )

    assert result.applied is True
    assert result.user_id == user_id
    assert result.plan_code == PlanCode.STARTER


@pytest.mark.asyncio
async def test_provider_none_is_rejected():
    service = BillingProviderStateService(
        None
    )

    with pytest.raises(
        ValueError,
        match="BillingProvider.NONE",
    ):
        await service.apply_verified_state(
            VerifiedProviderSubscriptionInput(
                user_id=uuid.uuid4(),
                provider=BillingProvider.NONE,
                provider_subscription_id="invalid",
                plan_code=PlanCode.STARTER,
                status=SubscriptionStatus.ACTIVE,
            )
        )