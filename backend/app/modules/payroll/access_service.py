from __future__ import annotations

import uuid

from fastapi import (
    HTTPException,
    status,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.modules.employees.repository import (
    EmployeeRepository,
)
from app.modules.payroll.models import (
    CompensationContract,
)
from app.modules.payroll.repository import (
    PayrollRepository,
)
from app.modules.workspace_permissions.permissions import (
    WorkspacePermission,
)
from app.modules.workspace_permissions.service import (
    WorkspacePermissionService,
)


class PayrollAccessService:
    """
    Payroll authorization + target-scope helper.

    Existing canonical permissions are used:

        PAYROLL_READ
        PAYROLL_MANAGE
        COMPENSATION_SELF_READ

    Payroll is intentionally not granted through generic employee
    visibility because salary/compensation is sensitive data.
    """

    def __init__(
        self,
        *,
        scope: object,
        session: AsyncSession,
    ) -> None:
        self.scope = scope

        self.session = session

        self.permissions = (
            WorkspacePermissionService(
                scope
            )
        )

        self.employees = (
            EmployeeRepository(
                session
            )
        )

        self.payroll = (
            PayrollRepository(
                session
            )
        )

    # =====================================================
    # WORKSPACE PAYROLL
    # =====================================================

    def require_payroll_read(
        self,
    ) -> None:
        self.permissions.require(
            WorkspacePermission
            .PAYROLL_READ
            .value
        )

    def require_payroll_manage(
        self,
    ) -> None:
        self.permissions.require(
            WorkspacePermission
            .PAYROLL_MANAGE
            .value
        )

    # =====================================================
    # ACTOR EMPLOYEE
    # =====================================================

    async def actor_employee(
        self,
    ):
        user_id = getattr(
            self.scope,
            "user_id",
            None,
        )

        if user_id is None:
            return None

        return await (
            self.employees
            .get_employee_by_user_id(
                user_id
            )
        )

    # =====================================================
    # COMPENSATION TARGET
    # =====================================================

    async def require_contract_read(
        self,
        contract_id: uuid.UUID,
    ) -> CompensationContract:
        contract = await (
            self.payroll.get_contract(
                contract_id
            )
        )

        if contract is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Compensation contract "
                    "not found."
                ),
            )

        if self.permissions.has(
            WorkspacePermission
            .PAYROLL_READ
            .value
        ):
            return contract

        actor = await (
            self.actor_employee()
        )

        if (
            actor is not None
            and actor.id
            == contract.employee_id
            and self.permissions.has(
                WorkspacePermission
                .COMPENSATION_SELF_READ
                .value
            )
        ):
            return contract

        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=(
                "Compensation data is "
                "outside the permitted "
                "scope."
            ),
        )

    async def require_employee_compensation_read(
        self,
        employee_id: uuid.UUID,
    ) -> None:
        if self.permissions.has(
            WorkspacePermission
            .PAYROLL_READ
            .value
        ):
            return

        actor = await (
            self.actor_employee()
        )

        if (
            actor is not None
            and actor.id
            == employee_id
            and self.permissions.has(
                WorkspacePermission
                .COMPENSATION_SELF_READ
                .value
            )
        ):
            return

        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=(
                "Compensation data is "
                "outside the permitted "
                "scope."
            ),
        )


__all__ = [
    "PayrollAccessService",
]