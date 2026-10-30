from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.core.exceptions import (
    ValidationError,
)
from app.modules.audit_log.models import (
    AUDIT_OUTCOMES,
    AUDIT_SEVERITIES,
    WorkspaceAuditEvent,
)
from app.modules.audit_log.repository import (
    AuditLogRepository,
)
from app.modules.audit_log.schemas import (
    AuditEventCreate,
    AuditEventListResponse,
    AuditEventResponse,
)


class AuditEventNotFoundError(
    LookupError
):
    pass


# =========================================================
# SECRET SANITIZATION
# =========================================================

_SENSITIVE_KEY_PARTS = (
    "password",
    "passwd",
    "secret",
    "token",
    "authorization",
    "cookie",
    "session",
    "api_key",
    "apikey",
    "private_key",
    "access_key",
    "refresh_key",
)


def _is_sensitive_key(
    key: str,
) -> bool:
    normalized = (
        key
        .strip()
        .lower()
    )

    return any(
        part in normalized
        for part
        in _SENSITIVE_KEY_PARTS
    )


def sanitize_audit_data(
    value,
):
    if isinstance(
        value,
        dict,
    ):
        cleaned = {}

        for (
            key,
            item,
        ) in value.items():
            key_text = str(
                key
            )

            if _is_sensitive_key(
                key_text
            ):
                cleaned[
                    key_text
                ] = "[REDACTED]"

            else:
                cleaned[
                    key_text
                ] = sanitize_audit_data(
                    item
                )

        return cleaned

    if isinstance(
        value,
        list,
    ):
        return [
            sanitize_audit_data(
                item
            )
            for item in value
        ]

    if isinstance(
        value,
        tuple,
    ):
        return [
            sanitize_audit_data(
                item
            )
            for item in value
        ]

    return value


class AuditLogService:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

        self.repository = (
            AuditLogRepository(
                session
            )
        )

    # =====================================================
    # SERIALIZE
    # =====================================================

    @staticmethod
    def _response(
        event: WorkspaceAuditEvent,
    ) -> AuditEventResponse:
        return (
            AuditEventResponse
            .model_validate(
                event
            )
        )

    # =====================================================
    # INTERNAL APPEND
    # =====================================================

    async def record(
        self,
        *,
        workspace_id: uuid.UUID,
        payload: AuditEventCreate,
    ) -> AuditEventResponse:
        outcome = (
            payload.outcome
            .strip()
            .lower()
        )

        severity = (
            payload.severity
            .strip()
            .lower()
        )

        if outcome not in AUDIT_OUTCOMES:
            raise ValidationError(
                "Invalid audit outcome."
            )

        if severity not in AUDIT_SEVERITIES:
            raise ValidationError(
                "Invalid audit severity."
            )

        category = (
            payload.category
            .strip()
            .lower()
        )

        action = (
            payload.action
            .strip()
            .lower()
        )

        if not category:
            raise ValidationError(
                "Audit category is required."
            )

        if not action:
            raise ValidationError(
                "Audit action is required."
            )

        event = WorkspaceAuditEvent(
            workspace_id=workspace_id,

            actor_user_id=(
                payload.actor_user_id
            ),

            category=category,

            action=action,

            outcome=outcome,

            severity=severity,

            target_type=(
                payload.target_type
                .strip()
                .lower()
                if payload.target_type
                else None
            ),

            target_id=(
                payload.target_id
            ),

            target_label=(
                payload.target_label
            ),

            message=payload.message,

            request_id=(
                payload.request_id
            ),

            ip_address=(
                payload.ip_address
            ),

            user_agent=(
                payload.user_agent
            ),

            event_data=(
                sanitize_audit_data(
                    payload.event_data
                )
            ),
        )

        event = await (
            self.repository.create(
                event
            )
        )

        # Do not commit here.
        #
        # Audit append should participate in the caller's
        # transaction when recording a role/member/admin
        # mutation. Caller owns commit/rollback.

        return self._response(
            event
        )

    # =====================================================
    # GET ONE
    # =====================================================

    async def get(
        self,
        *,
        workspace_id: uuid.UUID,
        event_id: uuid.UUID,
    ) -> AuditEventResponse:
        event = await (
            self.repository.get(
                workspace_id=workspace_id,
                event_id=event_id,
            )
        )

        if event is None:
            raise AuditEventNotFoundError(
                "Audit event was not found."
            )

        return self._response(
            event
        )

    # =====================================================
    # LIST
    # =====================================================

    async def list_events(
        self,
        *,
        workspace_id: uuid.UUID,
        category: str | None,
        action: str | None,
        actor_user_id: uuid.UUID | None,
        target_type: str | None,
        target_id: uuid.UUID | None,
        outcome: str | None,
        severity: str | None,
        start_at: datetime | None,
        end_at: datetime | None,
        limit: int,
        offset: int,
    ) -> AuditEventListResponse:
        if (
            start_at is not None
            and end_at is not None
            and start_at >= end_at
        ):
            raise ValidationError(
                "start_at must be earlier "
                "than end_at."
            )

        if (
            outcome is not None
            and outcome not in AUDIT_OUTCOMES
        ):
            raise ValidationError(
                "Invalid audit outcome."
            )

        if (
            severity is not None
            and severity not in AUDIT_SEVERITIES
        ):
            raise ValidationError(
                "Invalid audit severity."
            )

        (
            events,
            total,
        ) = await (
            self.repository.list_events(
                workspace_id=workspace_id,

                category=(
                    category
                    .strip()
                    .lower()
                    if category
                    else None
                ),

                action=(
                    action
                    .strip()
                    .lower()
                    if action
                    else None
                ),

                actor_user_id=(
                    actor_user_id
                ),

                target_type=(
                    target_type
                    .strip()
                    .lower()
                    if target_type
                    else None
                ),

                target_id=target_id,

                outcome=outcome,

                severity=severity,

                start_at=start_at,

                end_at=end_at,

                limit=limit,

                offset=offset,
            )
        )

        return AuditEventListResponse(
            items=[
                self._response(
                    event
                )
                for event
                in events
            ],

            total=total,

            limit=limit,

            offset=offset,
        )


__all__ = [
    "AuditEventNotFoundError",
    "sanitize_audit_data",
    "AuditLogService",
]