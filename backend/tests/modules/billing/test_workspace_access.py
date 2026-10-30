from __future__ import annotations

import uuid

import pytest

from app.modules.billing.entitlements import (
    AccountEntitlements,
)
from app.modules.billing.enums import (
    SubscriptionStatus,
)
from app.modules.billing.plans import PlanCode
from app.modules.billing.workspace_access import (
    WorkspaceEntitlementAccess,
)


class FakeGuard:
    def __init__(
        self,
        result: AccountEntitlements,
    ) -> None:
        self.result = result

        self.called = False

    async def require_allowed(
        self,
        session,
        *,
        user_id,
        workspace_count_loader,
    ) -> AccountEntitlements:
        self.called = True

        assert isinstance(
            user_id,
            uuid.UUID,
        )

        assert callable(
            workspace_count_loader
        )

        return self.result


@pytest.mark.asyncio
async def test_workspace_access_delegates_to_guard():
    expected = AccountEntitlements(
        plan_code=PlanCode.STARTER,
        subscription_status=(
            SubscriptionStatus.ACTIVE
        ),
        workspace_limit=1,
        workspace_count=0,
        create_workspace=True,
        monitoring=True,
        live_screen=False,
        advanced_analytics=False,
    )

    guard = FakeGuard(
        expected
    )

    service = WorkspaceEntitlementAccess(
        None,
        guard=guard,
    )

    result = (
        await service.require_workspace_creation(
            user_id=uuid.uuid4()
        )
    )

    assert guard.called is True
    assert result is expected