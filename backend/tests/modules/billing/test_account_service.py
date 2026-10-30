from __future__ import annotations

import uuid

import pytest

from app.modules.billing.account_service import (
    AccountBillingService,
)
from app.modules.billing.enums import (
    SubscriptionStatus,
)
from app.modules.billing.plans import PlanCode


class FakeSubscription:
    def __init__(
        self,
        *,
        plan_code: PlanCode,
        status: SubscriptionStatus,
    ) -> None:
        self.plan_code = (
            plan_code
        )

        self.status = (
            status
        )


class FakeRepository:
    def __init__(
        self,
        subscription,
    ) -> None:
        self.subscription = (
            subscription
        )

    async def get_subscription_for_user(
        self,
        session,
        *,
        user_id,
    ):
        return self.subscription


@pytest.mark.asyncio
async def test_missing_subscription_returns_free():
    service = AccountBillingService(
        repository=FakeRepository(
            None
        )
    )

    (
        plan,
        status,
    ) = await service.get_effective_subscription(
        None,
        user_id=uuid.uuid4(),
    )

    assert plan == PlanCode.FREE

    assert (
        status
        == SubscriptionStatus.NONE
    )


@pytest.mark.asyncio
async def test_active_starter_subscription():
    service = AccountBillingService(
        repository=FakeRepository(
            FakeSubscription(
                plan_code=PlanCode.STARTER,
                status=SubscriptionStatus.ACTIVE,
            )
        )
    )

    (
        plan,
        status,
    ) = await service.get_effective_subscription(
        None,
        user_id=uuid.uuid4(),
    )

    assert (
        plan
        == PlanCode.STARTER
    )

    assert (
        status
        == SubscriptionStatus.ACTIVE
    )


@pytest.mark.asyncio
async def test_entitlements_use_workspace_count():
    service = AccountBillingService(
        repository=FakeRepository(
            FakeSubscription(
                plan_code=PlanCode.STARTER,
                status=SubscriptionStatus.ACTIVE,
            )
        )
    )

    async def count_loader(
        session,
        user_id,
    ) -> int:
        return 1

    result = await service.get_entitlements(
        None,
        user_id=uuid.uuid4(),
        workspace_count_loader=count_loader,
    )

    assert (
        result.workspace_count
        == 1
    )

    assert (
        result.workspace_limit
        == 1
    )

    assert (
        result.create_workspace
        is False
    )