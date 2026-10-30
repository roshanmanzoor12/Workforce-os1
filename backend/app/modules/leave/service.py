from __future__ import annotations

import uuid
from datetime import (
    date,
    datetime,
    timedelta,
    timezone,
)

from fastapi import (
    HTTPException,
    status,
)
from sqlalchemy.exc import (
    IntegrityError,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.modules.employees.repository import (
    EmployeeRepository,
)
from app.modules.leave.balance_service import (
    LeaveBalanceService,
)
from app.modules.leave.calendar_service import (
    LeaveCalendarService,
)
from app.modules.leave.models import (
    LeaveBalance,
    LeavePolicy,
    LeaveRequest,
    LeaveRequestStatus,
    LeaveType,
)
from app.modules.leave.repository import (
    LeaveRepository,
)
from app.modules.leave.schemas import (
    LeaveBalanceAdjustmentRequest,
    LeavePolicyUpsertRequest,
    LeaveRequestCreateRequest,
    LeaveTypeCreateRequest,
    LeaveTypeUpdateRequest,
)


class LeaveService:
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

        self.employees = (
            EmployeeRepository(
                session
            )
        )

        self.balances = (
            LeaveBalanceService(
                session
            )
        )

        self.calendar = (
            LeaveCalendarService(
                session
            )
        )

    # =====================================================
    # LEAVE TYPES
    # =====================================================

    async def create_leave_type(
        self,
        request: LeaveTypeCreateRequest,
    ) -> LeaveType:
        code = (
            request.code
            .strip()
            .lower()
        )

        if (
            await self.repository
            .get_type_by_code(
                code
            )
            is not None
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "Leave type code "
                    "already exists."
                ),
            )

        item = LeaveType(
            name=(
                request.name.strip()
            ),
            code=code,
            description=(
                request.description.strip()
                if request.description
                else None
            ),
            is_paid=(
                request.is_paid
            ),
            requires_approval=(
                request
                .requires_approval
            ),
            is_active=True,
        )

        self.session.add(
            item
        )

        try:
            await self.session.commit()

        except IntegrityError as exc:
            await self.session.rollback()

            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "Leave type already "
                    "exists."
                ),
            ) from exc

        await self.session.refresh(
            item
        )

        return item

    async def update_leave_type(
        self,
        *,
        leave_type_id: uuid.UUID,
        request: LeaveTypeUpdateRequest,
    ) -> LeaveType:
        item = await (
            self.repository.get_type(
                leave_type_id
            )
        )

        if item is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Leave type not found."
                ),
            )

        patch = request.model_dump(
            exclude_unset=True
        )

        for (
            field_name,
            value,
        ) in patch.items():
            if isinstance(
                value,
                str,
            ):
                value = value.strip()

            setattr(
                item,
                field_name,
                value,
            )

        try:
            await self.session.commit()

        except IntegrityError as exc:
            await self.session.rollback()

            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "Leave type update "
                    "conflicts with existing "
                    "leave configuration."
                ),
            ) from exc

        await self.session.refresh(
            item
        )

        return item

    # =====================================================
    # POLICIES
    # =====================================================

    async def upsert_policy(
        self,
        *,
        leave_type_id: uuid.UUID,
        request: LeavePolicyUpsertRequest,
    ) -> LeavePolicy:
        leave_type = await (
            self.repository.get_type(
                leave_type_id
            )
        )

        if leave_type is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Leave type not found."
                ),
            )

        policy = await (
            self.repository.get_policy(
                leave_type_id=(
                    leave_type_id
                )
            )
        )

        if policy is None:
            policy = LeavePolicy(
                leave_type_id=(
                    leave_type_id
                ),
                annual_allowance_days=(
                    request
                    .annual_allowance_days
                ),
                carry_forward_days=(
                    request
                    .carry_forward_days
                ),
                minimum_notice_days=(
                    request
                    .minimum_notice_days
                ),
                allow_negative_balance=(
                    request
                    .allow_negative_balance
                ),
                is_active=(
                    request.is_active
                ),
            )

            self.session.add(
                policy
            )

        else:
            policy.annual_allowance_days = (
                request
                .annual_allowance_days
            )

            policy.carry_forward_days = (
                request
                .carry_forward_days
            )

            policy.minimum_notice_days = (
                request
                .minimum_notice_days
            )

            policy.allow_negative_balance = (
                request
                .allow_negative_balance
            )

            policy.is_active = (
                request.is_active
            )

        await self.session.commit()

        await self.session.refresh(
            policy
        )

        return policy

    # =====================================================
    # CREATE REQUEST
    # =====================================================

    async def create_request(
        self,
        *,
        employee_id: uuid.UUID,
        actor_user_id: uuid.UUID,
        request: LeaveRequestCreateRequest,
    ) -> LeaveRequest:
        employee = await (
            self.employees
            .get_employee_by_id(
                employee_id
            )
        )

        if (
            employee is None
            or not employee.is_active
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Active employee "
                    "not found."
                ),
            )

        leave_type = await (
            self.repository.get_type(
                request.leave_type_id
            )
        )

        if (
            leave_type is None
            or not leave_type.is_active
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Active leave type "
                    "not found."
                ),
            )

        # -------------------------------------------------
        # BALANCE YEAR CONTRACT
        # -------------------------------------------------

        if (
            request.start_date.year
            != request.end_date.year
        ):
            raise HTTPException(
                status_code=(
                    status
                    .HTTP_422_UNPROCESSABLE_ENTITY
                ),
                detail=(
                    "A leave request cannot "
                    "span multiple balance "
                    "years."
                ),
            )

        # -------------------------------------------------
        # OVERLAP
        # -------------------------------------------------

        if await (
            self.repository
            .has_overlapping_request(
                employee_id=employee_id,
                start_date=(
                    request.start_date
                ),
                end_date=(
                    request.end_date
                ),
            )
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "Employee already has "
                    "an overlapping pending "
                    "or approved leave request."
                ),
            )

        # -------------------------------------------------
        # POLICY
        # -------------------------------------------------

        policy = await (
            self.repository.get_policy(
                leave_type_id=(
                    leave_type.id
                )
            )
        )

        if (
            policy is not None
            and policy.is_active
            and policy.minimum_notice_days
            > 0
        ):
            minimum_start = (
                date.today()
                + timedelta(
                    days=(
                        policy
                        .minimum_notice_days
                    )
                )
            )

            if (
                request.start_date
                < minimum_start
            ):
                raise HTTPException(
                    status_code=(
                        status
                        .HTTP_422_UNPROCESSABLE_ENTITY
                    ),
                    detail=(
                        "Leave request does "
                        "not satisfy the "
                        "minimum notice policy."
                    ),
                )

        # -------------------------------------------------
        # AUTHORITATIVE SCHEDULE-AWARE DAY COUNT
        # -------------------------------------------------

        requested_days = await (
            self.calendar
            .chargeable_days(
                employee_id=employee_id,
                start_date=(
                    request.start_date
                ),
                end_date=(
                    request.end_date
                ),
            )
        )

        if requested_days <= 0:
            raise HTTPException(
                status_code=(
                    status
                    .HTTP_422_UNPROCESSABLE_ENTITY
                ),
                detail=(
                    "The selected leave range "
                    "contains no chargeable "
                    "scheduled working days."
                ),
            )

        # -------------------------------------------------
        # BALANCE
        # -------------------------------------------------

        balance = await (
            self.balances
            .get_or_create(
                employee_id=employee_id,
                leave_type_id=(
                    leave_type.id
                ),
                balance_year=(
                    request
                    .start_date
                    .year
                ),
                actor_user_id=(
                    actor_user_id
                ),
            )
        )

        try:
            await (
                self.balances
                .reserve_pending(
                    balance=balance,
                    requested_days=(
                        requested_days
                    ),
                    policy=policy,
                )
            )

        except ValueError as exc:
            await self.session.rollback()

            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=str(
                    exc
                ),
            ) from exc

        # -------------------------------------------------
        # REQUEST
        # -------------------------------------------------

        leave_request = LeaveRequest(
            employee_id=employee_id,
            leave_type_id=(
                leave_type.id
            ),
            start_date=(
                request.start_date
            ),
            end_date=(
                request.end_date
            ),
            requested_days=(
                requested_days
            ),
            status=(
                LeaveRequestStatus
                .PENDING
            ),
            reason=(
                request.reason.strip()
                if request.reason
                else None
            ),
            created_by_user_id=(
                actor_user_id
            ),
        )

        self.session.add(
            leave_request
        )

        await self.session.commit()

        await self.session.refresh(
            leave_request
        )

        return leave_request

    # =====================================================
    # APPROVE
    # =====================================================

    async def approve_request(
        self,
        *,
        request_id: uuid.UUID,
        reviewer_user_id: uuid.UUID,
        decision_note: (
            str | None
        ) = None,
    ) -> LeaveRequest:
        leave_request = await (
            self._require_pending_request(
                request_id
            )
        )

        balance = await (
            self.balances
            .get_or_create(
                employee_id=(
                    leave_request
                    .employee_id
                ),
                leave_type_id=(
                    leave_request
                    .leave_type_id
                ),
                balance_year=(
                    leave_request
                    .start_date
                    .year
                ),
                actor_user_id=(
                    reviewer_user_id
                ),
            )
        )

        await (
            self.balances
            .approve_pending(
                balance=balance,
                requested_days=(
                    leave_request
                    .requested_days
                ),
            )
        )

        leave_request.status = (
            LeaveRequestStatus
            .APPROVED
        )

        leave_request.decision_note = (
            decision_note.strip()
            if decision_note
            else None
        )

        leave_request.reviewed_by_user_id = (
            reviewer_user_id
        )

        leave_request.reviewed_at = (
            datetime.now(
                timezone.utc
            )
        )

        await self.session.commit()

        await self.session.refresh(
            leave_request
        )

        return leave_request

    # =====================================================
    # REJECT
    # =====================================================

    async def reject_request(
        self,
        *,
        request_id: uuid.UUID,
        reviewer_user_id: uuid.UUID,
        decision_note: (
            str | None
        ) = None,
    ) -> LeaveRequest:
        leave_request = await (
            self._require_pending_request(
                request_id
            )
        )

        await self._release_balance(
            leave_request=leave_request,
            actor_user_id=(
                reviewer_user_id
            ),
        )

        leave_request.status = (
            LeaveRequestStatus
            .REJECTED
        )

        leave_request.decision_note = (
            decision_note.strip()
            if decision_note
            else None
        )

        leave_request.reviewed_by_user_id = (
            reviewer_user_id
        )

        leave_request.reviewed_at = (
            datetime.now(
                timezone.utc
            )
        )

        await self.session.commit()

        await self.session.refresh(
            leave_request
        )

        return leave_request

    # =====================================================
    # CANCEL
    # =====================================================

    async def cancel_request(
        self,
        *,
        request_id: uuid.UUID,
        actor_user_id: uuid.UUID,
    ) -> LeaveRequest:
        leave_request = await (
            self.repository.get_request(
                request_id
            )
        )

        if leave_request is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Leave request not found."
                ),
            )

        if (
            leave_request.status
            != LeaveRequestStatus.PENDING
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "Only pending leave "
                    "requests can be cancelled."
                ),
            )

        await self._release_balance(
            leave_request=(
                leave_request
            ),
            actor_user_id=(
                actor_user_id
            ),
        )

        leave_request.status = (
            LeaveRequestStatus
            .CANCELLED
        )

        await self.session.commit()

        await self.session.refresh(
            leave_request
        )

        return leave_request

    # =====================================================
    # BALANCE ADJUSTMENT
    # =====================================================

    async def adjust_balance(
        self,
        *,
        employee_id: uuid.UUID,
        leave_type_id: uuid.UUID,
        balance_year: int,
        actor_user_id: uuid.UUID,
        request: (
            LeaveBalanceAdjustmentRequest
        ),
    ) -> LeaveBalance:
        employee = await (
            self.employees
            .get_employee_by_id(
                employee_id
            )
        )

        if employee is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Employee not found."
                ),
            )

        leave_type = await (
            self.repository.get_type(
                leave_type_id
            )
        )

        if leave_type is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Leave type not found."
                ),
            )

        balance = await (
            self.balances
            .get_or_create(
                employee_id=employee_id,
                leave_type_id=(
                    leave_type_id
                ),
                balance_year=(
                    balance_year
                ),
                actor_user_id=(
                    actor_user_id
                ),
            )
        )

        await self.balances.adjust(
            balance=balance,
            adjustment_days=(
                request.adjustment_days
            ),
            actor_user_id=(
                actor_user_id
            ),
        )

        await self.session.commit()

        await self.session.refresh(
            balance
        )

        return balance

    # =====================================================
    # INTERNAL
    # =====================================================

    async def _require_pending_request(
        self,
        request_id: uuid.UUID,
    ) -> LeaveRequest:
        leave_request = await (
            self.repository.get_request(
                request_id
            )
        )

        if leave_request is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Leave request not found."
                ),
            )

        if (
            leave_request.status
            != LeaveRequestStatus.PENDING
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "Leave request is no "
                    "longer pending."
                ),
            )

        return leave_request

    async def _release_balance(
        self,
        *,
        leave_request: LeaveRequest,
        actor_user_id: uuid.UUID,
    ) -> None:
        balance = await (
            self.balances
            .get_or_create(
                employee_id=(
                    leave_request
                    .employee_id
                ),
                leave_type_id=(
                    leave_request
                    .leave_type_id
                ),
                balance_year=(
                    leave_request
                    .start_date
                    .year
                ),
                actor_user_id=(
                    actor_user_id
                ),
            )
        )

        await (
            self.balances
            .release_pending(
                balance=balance,
                requested_days=(
                    leave_request
                    .requested_days
                ),
            )
        )


__all__ = [
    "LeaveService",
]