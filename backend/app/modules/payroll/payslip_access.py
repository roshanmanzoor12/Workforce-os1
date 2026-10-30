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
from app.modules.payroll.payslip_models import (
    PayrollPayslip,
)
from app.modules.payroll.payslip_service import (
    PayrollPayslipService,
)
from app.modules.workspace_permissions.permissions import (
    WorkspacePermission,
)
from app.modules.workspace_permissions.service import (
    WorkspacePermissionService,
)


class PayrollPayslipAccessService:
    def __init__(
        self,
        *,
        scope,
        session: AsyncSession,
    ) -> None:
        self.scope = scope

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

        self.payslips = (
            PayrollPayslipService(
                session
            )
        )

    async def require_self_employee(
        self,
    ):
        employee = await (
            self.employees
            .get_employee_by_user_id(
                self.scope.user_id
            )
        )

        if employee is None:
            raise HTTPException(
                status_code=(
                    status
                    .HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Employee record not found "
                    "for current user."
                ),
            )

        return employee

    async def require_read(
        self,
        payslip_id: uuid.UUID,
    ) -> PayrollPayslip:
        payslip = await (
            self.payslips
            .require_payslip(
                payslip_id
            )
        )

        if self.permissions.has(
            WorkspacePermission
            .PAYROLL_READ
            .value
        ):
            return payslip

        employee = await (
            self.require_self_employee()
        )

        if (
            employee.id
            == payslip.employee_id
            and self.permissions.has(
                WorkspacePermission
                .COMPENSATION_SELF_READ
                .value
            )
        ):
            return payslip

        raise HTTPException(
            status_code=(
                status
                .HTTP_403_FORBIDDEN
            ),
            detail=(
                "Payslip access denied."
            ),
        )


__all__ = [
    "PayrollPayslipAccessService",
]