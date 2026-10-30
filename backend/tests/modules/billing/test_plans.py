from app.modules.billing.plans import (
    PLAN_CATALOG,
    PlanCode,
    get_plan_definition,
)


def test_all_plan_codes_are_registered():
    assert set(PLAN_CATALOG) == set(PlanCode)


def test_starter_plan_allows_one_workspace():
    plan = get_plan_definition(
        PlanCode.STARTER
    )

    assert plan.workspace_limit == 1


def test_free_plan_does_not_allow_workspace():
    plan = get_plan_definition(
        PlanCode.FREE
    )

    assert plan.workspace_limit == 0


def test_business_plan_has_advanced_analytics():
    plan = get_plan_definition(
        PlanCode.BUSINESS
    )

    assert plan.advanced_analytics_enabled is True