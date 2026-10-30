from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import (
    func,
    or_,
    select,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.modules.leave.models import (
    LeaveBalance,
    LeavePolicy,
    LeaveRequest,
    LeaveRequestStatus,
    LeaveType,
)


class LeaveRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    # =====================================================
    # LEAVE TYPES
    # =====================================================

    async def list_types(
        self,
        *,
        active_only: bool = False,
    ) -> list[LeaveType]:
        statement = select(
            LeaveType
        )

        if active_only:
            statement = (
                statement.where(
                    LeaveType
                    .is_active
                    .is_(True)
                )
            )

        result = await (
            self.session.scalars(
                statement.order_by(
                    LeaveType.name.asc()
                )
            )
        )

        return list(
            result
        )

    async def get_type(
        self,
        leave_type_id: uuid.UUID,
    ) -> LeaveType | None:
        return await self.session.scalar(
            select(
                LeaveType
            ).where(
                LeaveType.id
                == leave_type_id
            )
        )

    async def get_type_by_code(
        self,
        code: str,
    ) -> LeaveType | None:
        return await self.session.scalar(
            select(
                LeaveType
            ).where(
                func.lower(
                    LeaveType.code
                )
                == code.strip().lower()
            )
        )

    # =====================================================
    # POLICIES
    # =====================================================

    async def get_policy(
        self,
        *,
        leave_type_id: uuid.UUID,
    ) -> LeavePolicy | None:
        return await self.session.scalar(
            select(
                LeavePolicy
            ).where(
                LeavePolicy.leave_type_id
                == leave_type_id
            )
        )

    async def list_policies(
        self,
    ) -> list[LeavePolicy]:
        result = await (
            self.session.scalars(
                select(
                    LeavePolicy
                ).order_by(
                    LeavePolicy
                    .created_at
                    .asc()
                )
            )
        )

        return list(
            result
        )

    # =====================================================
    # BALANCES
    # =====================================================

    async def get_balance(
        self,
        *,
        employee_id: uuid.UUID,
        leave_type_id: uuid.UUID,
        balance_year: int,
    ) -> LeaveBalance | None:
        return await self.session.scalar(
            select(
                LeaveBalance
            ).where(
                LeaveBalance.employee_id
                == employee_id,
                LeaveBalance.leave_type_id
                == leave_type_id,
                LeaveBalance.balance_year
                == balance_year,
            )
        )

    async def list_balances(
        self,
        *,
        employee_id: uuid.UUID,
        balance_year: (
            int | None
        ) = None,
    ) -> list[LeaveBalance]:
        statement = select(
            LeaveBalance
        ).where(
            LeaveBalance.employee_id
            == employee_id
        )

        if balance_year is not None:
            statement = statement.where(
                LeaveBalance.balance_year
                == balance_year
            )

        result = await (
            self.session.scalars(
                statement.order_by(
                    LeaveBalance
                    .balance_year
                    .desc(),
                    LeaveBalance
                    .created_at
                    .asc(),
                )
            )
        )

        return list(
            result
        )

    # =====================================================
    # REQUESTS
    # =====================================================

    async def get_request(
        self,
        request_id: uuid.UUID,
    ) -> LeaveRequest | None:
        return await self.session.scalar(
            select(
                LeaveRequest
            ).where(
                LeaveRequest.id
                == request_id
            )
        )

    async def list_requests(
        self,
        *,
        employee_id: (
            uuid.UUID | None
        ) = None,
        status: (
            LeaveRequestStatus | None
        ) = None,
        start_date: (
            date | None
        ) = None,
        end_date: (
            date | None
        ) = None,
    ) -> list[LeaveRequest]:
        statement = select(
            LeaveRequest
        )

        if employee_id is not None:
            statement = statement.where(
                LeaveRequest.employee_id
                == employee_id
            )

        if status is not None:
            statement = statement.where(
                LeaveRequest.status
                == status
            )

        if start_date is not None:
            statement = statement.where(
                LeaveRequest.end_date
                >= start_date
            )

        if end_date is not None:
            statement = statement.where(
                LeaveRequest.start_date
                <= end_date
            )

        result = await (
            self.session.scalars(
                statement.order_by(
                    LeaveRequest
                    .created_at
                    .desc()
                )
            )
        )

        return list(
            result
        )

    async def has_overlapping_request(
        self,
        *,
        employee_id: uuid.UUID,
        start_date: date,
        end_date: date,
        exclude_request_id: (
            uuid.UUID | None
        ) = None,
    ) -> bool:
        statement = (
            select(
                func.count()
            )
            .select_from(
                LeaveRequest
            )
            .where(
                LeaveRequest.employee_id
                == employee_id,
                LeaveRequest.status.in_(
                    [
                        LeaveRequestStatus
                        .PENDING,
                        LeaveRequestStatus
                        .APPROVED,
                    ]
                ),
                LeaveRequest.start_date
                <= end_date,
                LeaveRequest.end_date
                >= start_date,
            )
        )

        if (
            exclude_request_id
            is not None
        ):
            statement = statement.where(
                LeaveRequest.id
                != exclude_request_id
            )

        result = await (
            self.session.execute(
                statement
            )
        )

        return (
            int(
                result.scalar_one()
            )
            > 0
        )

    async def count_requests(
        self,
        *,
        employee_id: (
            uuid.UUID | None
        ) = None,
        status: (
            LeaveRequestStatus | None
        ) = None,
    ) -> int:
        statement = (
            select(
                func.count()
            )
            .select_from(
                LeaveRequest
            )
        )

        if employee_id is not None:
            statement = statement.where(
                LeaveRequest.employee_id
                == employee_id
            )

        if status is not None:
            statement = statement.where(
                LeaveRequest.status
                == status
            )

        result = await (
            self.session.execute(
                statement
            )
        )

        return int(
            result.scalar_one()
        )


__all__ = [
    "LeaveRepository",
]