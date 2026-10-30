from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class PlanCode(StrEnum):
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    BUSINESS = "business"


@dataclass(frozen=True, slots=True)
class PlanDefinition:
    code: PlanCode
    display_name: str
    workspace_limit: int
    member_limit_per_workspace: int
    monitoring_enabled: bool
    live_screen_enabled: bool
    advanced_analytics_enabled: bool


PLAN_CATALOG: dict[PlanCode, PlanDefinition] = {
    PlanCode.FREE: PlanDefinition(
        code=PlanCode.FREE,
        display_name="Free",
        workspace_limit=0,
        member_limit_per_workspace=0,
        monitoring_enabled=False,
        live_screen_enabled=False,
        advanced_analytics_enabled=False,
    ),
    PlanCode.STARTER: PlanDefinition(
        code=PlanCode.STARTER,
        display_name="Starter",
        workspace_limit=1,
        member_limit_per_workspace=10,
        monitoring_enabled=True,
        live_screen_enabled=True,
        advanced_analytics_enabled=False,
    ),
    PlanCode.PROFESSIONAL: PlanDefinition(
        code=PlanCode.PROFESSIONAL,
        display_name="Plus",
        workspace_limit=1,
        member_limit_per_workspace=100,
        monitoring_enabled=True,
        live_screen_enabled=True,
        advanced_analytics_enabled=False,
    ),
    PlanCode.BUSINESS: PlanDefinition(
        code=PlanCode.BUSINESS,
        display_name="Advanced",
        workspace_limit=3,
        member_limit_per_workspace=1000,
        monitoring_enabled=True,
        live_screen_enabled=True,
        advanced_analytics_enabled=True,
    ),
}


def get_plan_definition(
    plan_code: PlanCode,
) -> PlanDefinition:
    try:
        return PLAN_CATALOG[plan_code]
    except KeyError as exc:
        raise ValueError(
            f"Unsupported plan code: {plan_code}"
        ) from exc
