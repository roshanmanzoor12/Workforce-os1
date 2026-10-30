from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.modules.leave.models import (
    LeaveBalance,
    LeavePolicy,
)
from app.modules.leave.repository import (
    LeaveRepository,
)


ZERO = Decimal("0")


class LeaveBalanceService:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

        self.repository = (
            LeaveRepository(
                session
            )
        )

    async def get_or_create(
        self,
        *,
        employee_id: uuid.UUID,
        leave_type_id: uuid.UUID,
        balance_year: int,
        actor_user_id: (
            uuid.UUID | None
        ) = None,
    ) -> LeaveBalance:
        existing = await (
            self.repository
            .get_balance(
                employee_id=employee_id,
                leave_type_id=(
                    leave_type_id
                ),
                balance_year=(
                    balance_year
                ),
            )
        )

        if existing is not None:
            return existing

        policy = await (
            self.repository
            .get_policy(
                leave_type_id=(
                    leave_type_id
                )
            )
        )

        allocated = ZERO
        carried = ZERO

        if (
            policy is not None
            and policy.is_active
        ):
            allocated = (
                policy
                .annual_allowance_days
            )

            carried = (
                policy
                .carry_forward_days
            )

        balance = LeaveBalance(
            employee_id=employee_id,
            leave_type_id=(
                leave_type_id
            ),
            balance_year=balance_year,
            allocated_days=allocated,
            carried_forward_days=(
                carried
            ),
            adjustment_days=ZERO,
            used_days=ZERO,
            pending_days=ZERO,
            updated_by_user_id=(
                actor_user_id
            ),
        )

        self.session.add(
            balance
        )

        await self.session.flush()

        return balance

    @staticmethod
    def available_days(
        balance: LeaveBalance,
    ) -> Decimal:
        return (
            balance.allocated_days
            + balance.carried_forward_days
            + balance.adjustment_days
            - balance.used_days
            - balance.pending_days
        )

    async def reserve_pending(
        self,
        *,
        balance: LeaveBalance,
        requested_days: Decimal,
        policy: (
            LeavePolicy | None
        ),
    ) -> None:
        available = (
            self.available_days(
                balance
            )
        )

        allow_negative = (
            policy is not None
            and (
                policy
                .allow_negative_balance
            )
        )

        if (
            not allow_negative
            and requested_days
            > available
        ):
            raise ValueError(
                "Insufficient leave balance."
            )

        balance.pending_days = (
            balance.pending_days
            + requested_days
        )

        self.session.add(
            balance
        )

        await self.session.flush()

    async def approve_pending(
        self,
        *,
        balance: LeaveBalance,
        requested_days: Decimal,
    ) -> None:
        balance.pending_days = max(
            ZERO,
            balance.pending_days
            - requested_days,
        )

        balance.used_days = (
            balance.used_days
            + requested_days
        )

        self.session.add(
            balance
        )

        await self.session.flush()

    async def release_pending(
        self,
        *,
        balance: LeaveBalance,
        requested_days: Decimal,
    ) -> None:
        balance.pending_days = max(
            ZERO,
            balance.pending_days
            - requested_days,
        )

        self.session.add(
            balance
        )

        await self.session.flush()

    async def adjust(
        self,
        *,
        balance: LeaveBalance,
        adjustment_days: Decimal,
        actor_user_id: uuid.UUID,
    ) -> LeaveBalance:
        balance.adjustment_days = (
            balance.adjustment_days
            + adjustment_days
        )

        balance.updated_by_user_id = (
            actor_user_id
        )

        self.session.add(
            balance
        )

        await self.session.flush()

        return balance


__all__ = [
    "LeaveBalanceService",
]