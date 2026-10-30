from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from app.modules.billing.api_service import (
    BillingAPIService,
)
from app.modules.billing.entitlements import (
    AccountEntitlements,
)
from app.modules.billing.enums import (
    SubscriptionStatus,
)
from app.modules.billing.plans import PlanCode


class FakeSubscription:
    def __init__(
        self,
    ) -> None:
        self.plan_code = (
            PlanCode.PROFESSIONAL
        )

        self.status = (
            SubscriptionStatus.ACTIVE
        )

        self.current_period_start = datetime(
            2026,
            9,
            1,
            tzinfo=timezone.utc,
        )

        self.current_period_end = datetime(
            2026,
            10,
            1,
            tzinfo=timezone.utc,
        )


class FakeRepository:
    def __init__(
        self,
        subscription=None,
    ) -> None:
        self.subscription = subscription

    async def get_subscription_for_user(
        self,
        session,
        *,
        user_id,
    ):
        return self.subscription


class FakeAccountService:
    async def get_entitlements(
        self,
        session,
        *,
        user_id,
        workspace_count_loader,
    ) -> AccountEntitlements:
        return AccountEntitlements(
            plan_code=PlanCode.PROFESSIONAL,
            subscription_status=(
                SubscriptionStatus.ACTIVE
            ),
            workspace_limit=3,
            workspace_count=1,
            create_workspace=True,
            monitoring=True,
            live_screen=True,
            advanced_analytics=False,
        )


def test_list_plans():
    service = BillingAPIService(
        None,
        repository=FakeRepository(),
    )

    response = service.list_plans()

    assert len(response.plans) == 4

    assert response.plans[0].code == (
        PlanCode.FREE
    )

    assert response.plans[-1].code == (
        PlanCode.BUSINESS
    )


@pytest.mark.asyncio
async def test_missing_subscription_returns_free():
    service = BillingAPIService(
        None,
        repository=FakeRepository(
            None
        ),
    )

    response = (
        await service.get_current_subscription(
            user_id=uuid.uuid4()
        )
    )

    assert response.plan_code == (
        PlanCode.FREE
    )

    assert response.status == (
        SubscriptionStatus.NONE
    )


@pytest.mark.asyncio
async def test_current_subscription_returns_paid_plan():
    service = BillingAPIService(
        None,
        repository=FakeRepository(
            FakeSubscription()
        ),
    )

    response = (
        await service.get_current_subscription(
            user_id=uuid.uuid4()
        )
    )

    assert response.plan_code == (
        PlanCode.PROFESSIONAL
    )

    assert response.status == (
        SubscriptionStatus.ACTIVE
    )


@pytest.mark.asyncio
async def test_current_entitlements_are_safe():
    service = BillingAPIService(
        None,
        repository=FakeRepository(),
        account_service=FakeAccountService(),
    )

    response = (
        await service.get_current_entitlements(
            user_id=uuid.uuid4()
        )
    )

    assert response.workspace_limit == 3
    assert response.workspace_count == 1
    assert response.create_workspace is True
    assert response.monitoring is True
    assert response.live_screen is True
    assert response.advanced_analytics is False