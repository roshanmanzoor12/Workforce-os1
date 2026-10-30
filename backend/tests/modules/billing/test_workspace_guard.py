from __future__ import annotations

import uuid

import pytest

from app.modules.billing.entitlements import (
    AccountEntitlements,
)
from app.modules.billing.enums import (
    SubscriptionStatus,
)
from app.modules.billing.exceptions import (
    WorkspaceEntitlementDeniedError,
)
from app.modules.billing.plans import PlanCode
from app.modules.billing.workspace_guard import (
    WorkspaceCreationGuard,
)


class FakeBillingService:
    def __init__(
        self,
        entitlements: AccountEntitlements,
    ) -> None:
        self.entitlements = (
            entitlements
        )

    async def get_entitlements(
        self,
        session,
        *,
        user_id,
        workspace_count_loader,
    ) -> AccountEntitlements:
        return self.entitlements


def entitlement(
    *,
    create_workspace: bool,
    workspace_limit: int,
    workspace_count: int,
) -> AccountEntitlements:
    return AccountEntitlements(
        plan_code=PlanCode.STARTER,
        subscription_status=SubscriptionStatus.ACTIVE,
        workspace_limit=workspace_limit,
        workspace_count=workspace_count,
        create_workspace=create_workspace,
        monitoring=True,
        live_screen=False,
        advanced_analytics=False,
    )


async def unused_loader(
    session,
    user_id,
) -> int:
    return 0


@pytest.mark.asyncio
async def test_guard_allows_workspace_creation():
    guard = WorkspaceCreationGuard(
        billing_service=FakeBillingService(
            entitlement(
                create_workspace=True,
                workspace_limit=1,
                workspace_count=0,
            )
        )
    )

    result = await guard.require_allowed(
        None,
        user_id=uuid.uuid4(),
        workspace_count_loader=unused_loader,
    )

    assert result.create_workspace is True


@pytest.mark.asyncio
async def test_guard_rejects_plan_without_workspace():
    guard = WorkspaceCreationGuard(
        billing_service=FakeBillingService(
            entitlement(
                create_workspace=False,
                workspace_limit=0,
                workspace_count=0,
            )
        )
    )

    with pytest.raises(
        WorkspaceEntitlementDeniedError,
        match=(
            "Current plan does not include"
        ),
    ):
        await guard.require_allowed(
            None,
            user_id=uuid.uuid4(),
            workspace_count_loader=unused_loader,
        )


@pytest.mark.asyncio
async def test_guard_rejects_workspace_limit():
    guard = WorkspaceCreationGuard(
        billing_service=FakeBillingService(
            entitlement(
                create_workspace=False,
                workspace_limit=1,
                workspace_count=1,
            )
        )
    )

    with pytest.raises(
        WorkspaceEntitlementDeniedError,
        match="Workspace limit reached",
    ):
        await guard.require_allowed(
            None,
            user_id=uuid.uuid4(),
            workspace_count_loader=unused_loader,
        )