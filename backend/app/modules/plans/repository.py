from __future__ import annotations

from threading import RLock
from uuid import UUID

from app.modules.plans.models import Plan


class PlanRepository:
    def __init__(self) -> None:
        self._plans: dict[UUID, Plan] = {}
        self._lock = RLock()

    def list(self, *, active_only: bool = False) -> list[Plan]:
        with self._lock:
            plans = list(self._plans.values())

        if active_only:
            plans = [plan for plan in plans if plan.is_active]

        return sorted(plans, key=lambda plan: (plan.name.lower(), str(plan.id)))

    def get(self, plan_id: UUID) -> Plan | None:
        with self._lock:
            return self._plans.get(plan_id)

    def get_by_code(self, code: str) -> Plan | None:
        normalized = code.strip().lower()

        with self._lock:
            for plan in self._plans.values():
                if plan.code.lower() == normalized:
                    return plan

        return None

    def save(self, plan: Plan) -> Plan:
        with self._lock:
            self._plans[plan.id] = plan

        return plan