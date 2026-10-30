from __future__ import annotations

import uuid

import pytest

from app.modules.billing.billing_snapshot import (
    BillingSnapshotService,
)
from app.modules.billing.entitlements import (
    AccountEntitlements,
)
from app.modules.billing.enums import (
    SubscriptionStatus,
)
from app.modules.billing.plans import (
    PlanCode,
)


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


@pytest.mark.asyncio
async def test_snapshot_maps_entitlements():
    user_id = uuid.uuid4()

    service = BillingSnapshotService(
        None,
        account_service=(
            FakeAccountService()
        ),
    )

    snapshot = await service.get_snapshot(
        user_id=user_id
    )

    assert snapshot.user_id == user_id

    assert (
        snapshot.plan_code
        == PlanCode.PROFESSIONAL
    )

    assert snapshot.workspace_limit == 3

    assert snapshot.workspace_count == 1

    assert (
        snapshot.can_create_workspace
        is True
    )

    assert (
        snapshot.monitoring_enabled
        is True
    )

    assert (
        snapshot.live_screen_enabled
        is True
    )