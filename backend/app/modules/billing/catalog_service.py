from __future__ import annotations

from .plans import (
    PLAN_CATALOG,
    PlanCode,
    PlanDefinition,
)


class BillingCatalogService:
    def list_plans(
        self,
    ) -> tuple[
        PlanDefinition,
        ...,
    ]:
        ordered_codes = (
            PlanCode.FREE,
            PlanCode.STARTER,
            PlanCode.PROFESSIONAL,
            PlanCode.BUSINESS,
        )

        return tuple(
            PLAN_CATALOG[
                code
            ]
            for code in ordered_codes
        )

    def get_plan(
        self,
        plan_code: PlanCode,
    ) -> PlanDefinition:
        return PLAN_CATALOG[
            plan_code
        ]


__all__ = [
    "BillingCatalogService",
]