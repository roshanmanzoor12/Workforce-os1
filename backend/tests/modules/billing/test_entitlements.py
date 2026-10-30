import pytest

from app.modules.billing.entitlements import (
    evaluate_account_entitlements,
)
from app.modules.billing.enums import (
    SubscriptionStatus,
)
from app.modules.billing.plans import PlanCode


def test_free_plan_cannot_create_workspace():
    result = evaluate_account_entitlements(
        plan_code=PlanCode.FREE,
        subscription_status=SubscriptionStatus.NONE,
        workspace_count=0,
    )

    assert result.create_workspace is False
    assert result.monitoring is False


def test_starter_active_can_create_first_workspace():
    result = evaluate_account_entitlements(
        plan_code=PlanCode.STARTER,
        subscription_status=SubscriptionStatus.ACTIVE,
        workspace_count=0,
    )

    assert result.create_workspace is True
    assert result.workspace_limit == 1
    assert result.monitoring is True


def test_starter_cannot_create_second_workspace():
    result = evaluate_account_entitlements(
        plan_code=PlanCode.STARTER,
        subscription_status=SubscriptionStatus.ACTIVE,
        workspace_count=1,
    )

    assert result.create_workspace is False


def test_past_due_subscription_disables_paid_entitlements():
    result = evaluate_account_entitlements(
        plan_code=PlanCode.PROFESSIONAL,
        subscription_status=SubscriptionStatus.PAST_DUE,
        workspace_count=0,
    )

    assert result.create_workspace is False
    assert result.monitoring is False
    assert result.live_screen is False


def test_professional_active_enables_live_screen():
    result = evaluate_account_entitlements(
        plan_code=PlanCode.PROFESSIONAL,
        subscription_status=SubscriptionStatus.ACTIVE,
        workspace_count=0,
    )

    assert result.monitoring is True
    assert result.live_screen is True
    assert result.advanced_analytics is False


def test_business_active_enables_advanced_analytics():
    result = evaluate_account_entitlements(
        plan_code=PlanCode.BUSINESS,
        subscription_status=SubscriptionStatus.ACTIVE,
        workspace_count=0,
    )

    assert result.advanced_analytics is True


def test_workspace_count_cannot_be_negative():
    with pytest.raises(ValueError):
        evaluate_account_entitlements(
            plan_code=PlanCode.STARTER,
            subscription_status=SubscriptionStatus.ACTIVE,
            workspace_count=-1,
        )