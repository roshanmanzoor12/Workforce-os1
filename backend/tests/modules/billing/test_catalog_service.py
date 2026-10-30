from app.modules.billing.catalog_service import (
    BillingCatalogService,
)
from app.modules.billing.plans import (
    PlanCode,
)


def test_catalog_returns_expected_order():
    service = BillingCatalogService()

    plans = service.list_plans()

    assert [
        plan.code
        for plan in plans
    ] == [
        PlanCode.FREE,
        PlanCode.STARTER,
        PlanCode.PROFESSIONAL,
        PlanCode.BUSINESS,
    ]


def test_catalog_returns_starter():
    service = BillingCatalogService()

    plan = service.get_plan(
        PlanCode.STARTER
    )

    assert (
        plan.code
        == PlanCode.STARTER
    )

    assert (
        plan.workspace_limit
        == 1
    )


def test_catalog_business_has_monitoring():
    service = BillingCatalogService()

    plan = service.get_plan(
        PlanCode.BUSINESS
    )

    assert (
        plan.monitoring_enabled
        is True
    )

    assert (
        plan.advanced_analytics_enabled
        is True
    )