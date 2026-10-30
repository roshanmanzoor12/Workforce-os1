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
from app.modules.billing.provider_event import (
    VerifiedBillingProviderEvent,
)
from app.modules.billing.provider_event_service import (
    BillingProviderEventService,
)
from app.modules.billing.provider_schemas import (
    ProviderSubscriptionApplyResult,
)


class FakeCustomerService:
    def __init__(
        self,
    ) -> None:
        self.called = False

    async def apply_provider_customer(
        self,
        *,
        user_id,
        provider,
        provider_customer_id,
    ):
        self.called = True

        assert provider_customer_id == (
            "cus_test"
        )


class FakeStateService:
    def __init__(
        self,
    ) -> None:
        self.called = False

    async def apply_verified_state(
        self,
        request,
    ):
        self.called = True

        return ProviderSubscriptionApplyResult(
            user_id=request.user_id,
            plan_code=request.plan_code,
            status=request.status,
            applied=True,
        )


@pytest.mark.asyncio
async def test_verified_provider_event_applies_both_states():
    customer_service = (
        FakeCustomerService()
    )

    state_service = (
        FakeStateService()
    )

    service = BillingProviderEventService(
        None,
        customer_service=(
            customer_service
        ),
        state_service=(
            state_service
        ),
    )

    user_id = uuid.uuid4()

    result = await service.apply_verified_event(
        VerifiedBillingProviderEvent(
            event_id="evt_test",
            user_id=user_id,
            provider=BillingProvider.STRIPE,
            provider_customer_id="cus_test",
            provider_subscription_id="sub_test",
            plan_code=PlanCode.STARTER,
            subscription_status=(
                SubscriptionStatus.ACTIVE
            ),
        )
    )

    assert customer_service.called is True

    assert state_service.called is True

    assert result.applied is True

    assert (
        result.plan_code
        == PlanCode.STARTER
    )


@pytest.mark.asyncio
async def test_provider_none_event_rejected():
    service = BillingProviderEventService(
        None,
        customer_service=(
            FakeCustomerService()
        ),
        state_service=(
            FakeStateService()
        ),
    )

    with pytest.raises(
        ValueError,
        match="BillingProvider.NONE",
    ):
        await service.apply_verified_event(
            VerifiedBillingProviderEvent(
                event_id="evt_invalid",
                user_id=uuid.uuid4(),
                provider=BillingProvider.NONE,
                provider_customer_id="none",
                provider_subscription_id="none",
                plan_code=PlanCode.STARTER,
                subscription_status=(
                    SubscriptionStatus.ACTIVE
                ),
            )
        )