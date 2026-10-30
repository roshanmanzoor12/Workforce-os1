from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.modules.audit_log.schemas import (
    AuditEventCreate,
)
from app.modules.audit_log.service import (
    AuditLogService,
)


PAYROLL_AUDIT_CATEGORY = (
    "payroll"
)


class PayrollAuditService:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

        self.audit = AuditLogService(
            session
        )

    async def _record(
        self,
        *,
        workspace_id: uuid.UUID,
        actor_user_id: uuid.UUID,
        action: str,
        target_type: str,
        target_id: uuid.UUID,
        message: str,
        event_data: dict | None = None,
    ) -> None:
        try:
            await self.audit.record(
                workspace_id=workspace_id,
                payload=AuditEventCreate(
                    actor_user_id=(
                        actor_user_id
                    ),
                    category=(
                        PAYROLL_AUDIT_CATEGORY
                    ),
                    action=action,
                    outcome="success",
                    severity="info",
                    target_type=(
                        target_type
                    ),
                    target_id=(
                        target_id
                    ),
                    message=message,
                    event_data=(
                        event_data
                        or {}
                    ),
                ),
            )

            await self.session.commit()

        except Exception:
            await self.session.rollback()

    async def compensation_created(
        self,
        *,
        workspace_id: uuid.UUID,
        actor_user_id: uuid.UUID,
        contract_id: uuid.UUID,
        employee_id: uuid.UUID,
    ) -> None:
        await self._record(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action=(
                "compensation.contract.created"
            ),
            target_type=(
                "compensation_contract"
            ),
            target_id=contract_id,
            message=(
                "Compensation contract created."
            ),
            event_data={
                "employee_id": str(
                    employee_id
                ),
            },
        )

    async def compensation_updated(
        self,
        *,
        workspace_id: uuid.UUID,
        actor_user_id: uuid.UUID,
        contract_id: uuid.UUID,
        employee_id: uuid.UUID,
    ) -> None:
        await self._record(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action=(
                "compensation.contract.updated"
            ),
            target_type=(
                "compensation_contract"
            ),
            target_id=contract_id,
            message=(
                "Compensation contract updated."
            ),
            event_data={
                "employee_id": str(
                    employee_id
                ),
            },
        )

    async def run_created(
        self,
        *,
        workspace_id: uuid.UUID,
        actor_user_id: uuid.UUID,
        run_id: uuid.UUID,
    ) -> None:
        await self._record(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action="payroll.run.created",
            target_type="payroll_run",
            target_id=run_id,
            message="Payroll run created.",
        )

    async def run_calculated(
        self,
        *,
        workspace_id: uuid.UUID,
        actor_user_id: uuid.UUID,
        run_id: uuid.UUID,
        processed_employees: int,
        skipped_employees: int,
    ) -> None:
        await self._record(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action=(
                "payroll.run.calculated"
            ),
            target_type="payroll_run",
            target_id=run_id,
            message=(
                "Payroll run calculated."
            ),
            event_data={
                "processed_employees": (
                    processed_employees
                ),
                "skipped_employees": (
                    skipped_employees
                ),
            },
        )

    async def adjustment_created(
        self,
        *,
        workspace_id: uuid.UUID,
        actor_user_id: uuid.UUID,
        adjustment_id: uuid.UUID,
        run_id: uuid.UUID,
        employee_id: uuid.UUID,
    ) -> None:
        await self._record(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action=(
                "payroll.adjustment.created"
            ),
            target_type=(
                "payroll_adjustment"
            ),
            target_id=adjustment_id,
            message=(
                "Payroll adjustment created."
            ),
            event_data={
                "run_id": str(
                    run_id
                ),
                "employee_id": str(
                    employee_id
                ),
            },
        )

    async def run_approved(
        self,
        *,
        workspace_id: uuid.UUID,
        actor_user_id: uuid.UUID,
        run_id: uuid.UUID,
    ) -> None:
        await self._record(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action="payroll.run.approved",
            target_type="payroll_run",
            target_id=run_id,
            message="Payroll run approved.",
        )

    async def run_locked(
        self,
        *,
        workspace_id: uuid.UUID,
        actor_user_id: uuid.UUID,
        run_id: uuid.UUID,
    ) -> None:
        await self._record(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action="payroll.run.locked",
            target_type="payroll_run",
            target_id=run_id,
            message="Payroll run locked.",
        )

    async def run_paid(
        self,
        *,
        workspace_id: uuid.UUID,
        actor_user_id: uuid.UUID,
        run_id: uuid.UUID,
    ) -> None:
        await self._record(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action="payroll.run.paid",
            target_type="payroll_run",
            target_id=run_id,
            message=(
                "Payroll run marked paid."
            ),
        )


__all__ = [
    "PAYROLL_AUDIT_CATEGORY",
    "PayrollAuditService",
]