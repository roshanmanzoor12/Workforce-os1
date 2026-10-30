from uuid import uuid4

import pytest

from app.modules.plans.models import Plan
from app.modules.plans.repository import PlanRepository
from app.modules.plans.router import router
from app.modules.plans.schemas import PlanCreate
from app.modules.plans.service import (
    DuplicatePlanCodeError,
    PlanService,
)


def test_plan_router_exposes_expected_routes() -> None:
    paths = {route.path for route in router.routes}

    assert "/plans" in paths
    assert "/plans/{plan_id}" in paths
    assert "/plans/{plan_id}/activate" in paths
    assert "/plans/{plan_id}/deactivate" in paths
    assert "/plans/{plan_id}/check-limit" in paths


def test_plan_schema_accepts_valid_payload() -> None:
    payload = PlanCreate(
        code="pro",
        name="Professional",
        description="Professional workforce plan",
        monthly_price_cents=1999,
        features={"analytics": True},
        limits={"employees": 100},
    )

    assert payload.code == "pro"
    assert payload.monthly_price_cents == 1999
    assert payload.limits["employees"] == 100


def test_plan_service_creates_and_rejects_duplicate_codes() -> None:
    service = PlanService(PlanRepository())

    payload = PlanCreate(
        code="starter",
        name="Starter",
        monthly_price_cents=0,
    )

    plan = service.create_plan(payload)

    assert isinstance(plan, Plan)
    assert plan.code == "starter"
    assert plan.is_active is True

    with pytest.raises(DuplicatePlanCodeError):
        service.create_plan(payload)


def test_plan_limit_check() -> None:
    service = PlanService(PlanRepository())

    plan = service.create_plan(
        PlanCreate(
            code="team",
            name="Team",
            limits={"employees": 10},
        )
    )

    configured_limit, allowed = service.check_limit(
        plan.id,
        feature="employees",
        current_usage=8,
    )

    assert configured_limit == 10
    assert allowed is True

    configured_limit, allowed = service.check_limit(
        plan.id,
        feature="employees",
        current_usage=11,
    )

    assert configured_limit == 10
    assert allowed is False


def test_unconfigured_limit_is_allowed() -> None:
    service = PlanService(PlanRepository())

    plan = service.create_plan(
        PlanCreate(
            code=f"custom-{uuid4().hex[:8]}",
            name="Custom",
        )
    )

    configured_limit, allowed = service.check_limit(
        plan.id,
        feature="unknown_feature",
        current_usage=999999,
    )

    assert configured_limit is None
    assert allowed is True