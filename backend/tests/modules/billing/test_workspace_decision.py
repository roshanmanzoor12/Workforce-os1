from app.modules.billing.entitlements import (
    AccountEntitlements,
)
from app.modules.billing.enums import (
    SubscriptionStatus,
)
from app.modules.billing.plans import PlanCode
from app.modules.billing.workspace_decision import (
    build_workspace_creation_decision,
)


def make_entitlements(
    *,
    allowed: bool,
    workspace_limit: int,
    workspace_count: int,
) -> AccountEntitlements:
    return AccountEntitlements(
        plan_code=PlanCode.STARTER,
        subscription_status=(
            SubscriptionStatus.ACTIVE
        ),
        workspace_limit=workspace_limit,
        workspace_count=workspace_count,
        create_workspace=allowed,
        monitoring=True,
        live_screen=False,
        advanced_analytics=False,
    )


def test_allowed_workspace_creation():
    decision = (
        build_workspace_creation_decision(
            make_entitlements(
                allowed=True,
                workspace_limit=1,
                workspace_count=0,
            )
        )
    )

    assert decision.allowed is True
    assert decision.reason is None


def test_plan_without_workspace_is_denied():
    decision = (
        build_workspace_creation_decision(
            make_entitlements(
                allowed=False,
                workspace_limit=0,
                workspace_count=0,
            )
        )
    )

    assert decision.allowed is False

    assert (
        "does not include"
        in str(decision.reason)
    )


def test_limit_reached_is_denied():
    decision = (
        build_workspace_creation_decision(
            make_entitlements(
                allowed=False,
                workspace_limit=1,
                workspace_count=1,
            )
        )
    )

    assert decision.allowed is False

    assert (
        "limit reached"
        in str(decision.reason).lower()
    )