from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from app.modules.plans.models import Plan
from app.modules.plans.repository import PlanRepository
from app.modules.plans.schemas import PlanCreate, PlanUpdate


class PlanNotFoundError(LookupError):
    pass


class DuplicatePlanCodeError(ValueError):
    pass


class PlanService:
    def __init__(self, repository: PlanRepository | None = None) -> None:
        self.repository = repository or PlanRepository()

    def list_plans(self, *, active_only: bool = False) -> list[Plan]:
        return self.repository.list(active_only=active_only)

    def get_plan(self, plan_id: UUID) -> Plan:
        plan = self.repository.get(plan_id)

        if plan is None:
            raise PlanNotFoundError(f"Plan {plan_id} was not found")

        return plan

    def create_plan(self, payload: PlanCreate) -> Plan:
        if self.repository.get_by_code(payload.code) is not None:
            raise DuplicatePlanCodeError(
                f"Plan code '{payload.code}' already exists"
            )

        now = datetime.now(timezone.utc)

        plan = Plan(
            code=payload.code.strip().lower(),
            name=payload.name.strip(),
            description=payload.description,
            monthly_price_cents=payload.monthly_price_cents,
            features=dict(payload.features),
            limits=dict(payload.limits),
            is_active=True,
            created_at=now,
            updated_at=now,
        )

        return self.repository.save(plan)

    def update_plan(self, plan_id: UUID, payload: PlanUpdate) -> Plan:
        plan = self.get_plan(plan_id)

        if payload.name is not None:
            plan.name = payload.name.strip()

        if payload.description is not None:
            plan.description = payload.description

        if payload.monthly_price_cents is not None:
            plan.monthly_price_cents = payload.monthly_price_cents

        if payload.features is not None:
            plan.features = dict(payload.features)

        if payload.limits is not None:
            plan.limits = dict(payload.limits)

        plan.updated_at = datetime.now(timezone.utc)

        return self.repository.save(plan)

    def set_active(self, plan_id: UUID, active: bool) -> Plan:
        plan = self.get_plan(plan_id)
        plan.is_active = active
        plan.updated_at = datetime.now(timezone.utc)

        return self.repository.save(plan)

    def check_limit(
        self,
        plan_id: UUID,
        *,
        feature: str,
        current_usage: int | float,
    ) -> tuple[int | float | None, bool]:
        plan = self.get_plan(plan_id)
        configured_limit = plan.limits.get(feature)

        if configured_limit is None:
            return None, True

        return configured_limit, current_usage <= configured_limit