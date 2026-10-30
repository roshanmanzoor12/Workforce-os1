from __future__ import annotations

import logging
import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.modules.audit_log.schemas import (
    AuditEventCreate,
)
from app.modules.audit_log.service import (
    AuditLogService,
)
from app.modules.leave.models import (
    LeaveRequest,
)
from app.modules.leave.events import (
    LEAVE_BALANCE_ADJUSTED_EVENT,
    LEAVE_POLICY_UPDATED_EVENT,
    LEAVE_REQUEST_APPROVED_EVENT,
    LEAVE_REQUEST_CANCELLED_EVENT,
    LEAVE_REQUEST_CREATED_EVENT,
    LEAVE_REQUEST_REJECTED_EVENT,
)


logger = logging.getLogger(
    __name__
)


async def _append_leave_audit(
    *,
    control_session: AsyncSession,
    workspace_id: uuid.UUID,
    actor_user_id: uuid.UUID,
    action: str,
    target_type: str,
    target_id: uuid.UUID,
    target_label: str,
    event_data: dict,
) -> None:
    """
    Append control-plane audit after the tenant mutation commits.

    The tenant DB and control DB are separate transaction
    boundaries, so an audit failure is logged rather than
    rolling back an already committed tenant mutation.
    """

    try:
        await AuditLogService(
            control_session
        ).record(
            workspace_id=(
                workspace_id
            ),
            payload=AuditEventCreate(
                actor_user_id=(
                    actor_user_id
                ),
                category="leave",
                action=action,
                target_type=(
                    target_type
                ),
                target_id=target_id,
                target_label=(
                    target_label
                ),
                event_data=(
                    event_data
                ),
            ),
        )

        await control_session.commit()

    except Exception:
        await control_session.rollback()

        logger.exception(
            "Unable to persist leave "
            "audit event."
        )


async def audit_leave_request_created(
    *,
    control_session: AsyncSession,
    workspace_id: uuid.UUID,
    actor_user_id: uuid.UUID,
    leave_request: LeaveRequest,
) -> None:
    await _append_leave_audit(
        control_session=(
            control_session
        ),
        workspace_id=workspace_id,
        actor_user_id=(
            actor_user_id
        ),
        action=(
            LEAVE_REQUEST_CREATED_EVENT
        ),
        target_type=(
            "leave_request"
        ),
        target_id=(
            leave_request.id
        ),
        target_label=(
            "Leave request"
        ),
        event_data={
            "employee_id": str(
                leave_request.employee_id
            ),
            "leave_type_id": str(
                leave_request.leave_type_id
            ),
            "start_date": (
                leave_request
                .start_date
                .isoformat()
            ),
            "end_date": (
                leave_request
                .end_date
                .isoformat()
            ),
            "requested_days": str(
                leave_request
                .requested_days
            ),
        },
    )


async def audit_leave_request_decision(
    *,
    control_session: AsyncSession,
    workspace_id: uuid.UUID,
    actor_user_id: uuid.UUID,
    leave_request: LeaveRequest,
    approved: bool,
) -> None:
    action = (
        LEAVE_REQUEST_APPROVED_EVENT
        if approved
        else LEAVE_REQUEST_REJECTED_EVENT
    )

    await _append_leave_audit(
        control_session=(
            control_session
        ),
        workspace_id=workspace_id,
        actor_user_id=(
            actor_user_id
        ),
        action=action,
        target_type=(
            "leave_request"
        ),
        target_id=(
            leave_request.id
        ),
        target_label=(
            "Leave request"
        ),
        event_data={
            "employee_id": str(
                leave_request.employee_id
            ),
            "status": (
                leave_request.status.value
            ),
        },
    )


async def audit_leave_request_cancelled(
    *,
    control_session: AsyncSession,
    workspace_id: uuid.UUID,
    actor_user_id: uuid.UUID,
    leave_request: LeaveRequest,
) -> None:
    await _append_leave_audit(
        control_session=(
            control_session
        ),
        workspace_id=workspace_id,
        actor_user_id=(
            actor_user_id
        ),
        action=(
            LEAVE_REQUEST_CANCELLED_EVENT
        ),
        target_type=(
            "leave_request"
        ),
        target_id=(
            leave_request.id
        ),
        target_label=(
            "Leave request"
        ),
        event_data={
            "employee_id": str(
                leave_request.employee_id
            ),
        },
    )


async def audit_leave_policy_updated(
    *,
    control_session: AsyncSession,
    workspace_id: uuid.UUID,
    actor_user_id: uuid.UUID,
    leave_type_id: uuid.UUID,
) -> None:
    await _append_leave_audit(
        control_session=(
            control_session
        ),
        workspace_id=workspace_id,
        actor_user_id=(
            actor_user_id
        ),
        action=(
            LEAVE_POLICY_UPDATED_EVENT
        ),
        target_type=(
            "leave_type"
        ),
        target_id=leave_type_id,
        target_label=(
            "Leave policy"
        ),
        event_data={},
    )


async def audit_leave_balance_adjusted(
    *,
    control_session: AsyncSession,
    workspace_id: uuid.UUID,
    actor_user_id: uuid.UUID,
    employee_id: uuid.UUID,
    leave_type_id: uuid.UUID,
    balance_id: uuid.UUID,
    adjustment_days: Decimal,
    balance_year: int,
) -> None:
    await _append_leave_audit(
        control_session=(
            control_session
        ),
        workspace_id=workspace_id,
        actor_user_id=(
            actor_user_id
        ),
        action=(
            LEAVE_BALANCE_ADJUSTED_EVENT
        ),
        target_type=(
            "leave_balance"
        ),
        target_id=balance_id,
        target_label=(
            "Leave balance"
        ),
        event_data={
            "employee_id": str(
                employee_id
            ),
            "leave_type_id": str(
                leave_type_id
            ),
            "balance_year": (
                balance_year
            ),
            "adjustment_days": str(
                adjustment_days
            ),
        },
    )


__all__ = [
    "audit_leave_request_created",
    "audit_leave_request_decision",
    "audit_leave_request_cancelled",
    "audit_leave_policy_updated",
    "audit_leave_balance_adjusted",
]