from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.api_keys.audit_models import APIKeyAuditOutbox
from app.modules.api_keys.audit_repository import APIKeyAuditRepository
from app.modules.audit_log.models import WorkspaceAuditEvent


class APIKeyAuditDeliveryError(RuntimeError):
    pass


class APIKeyAuditDelivery:
    """
    Deliver tenant outbox events to the control audit database.

    The control transaction commits before the tenant transaction.
    A retry uses the same audit event ID, so a crash between the
    two commits does not create another control audit event.

    Sessions must be dedicated to this delivery operation.
    The caller must verify the physical tenant identity first.
    """

    def __init__(
        self,
        *,
        tenant_session: AsyncSession,
        control_session: AsyncSession,
        workspace_id: UUID,
    ) -> None:
        self.tenant_session = tenant_session
        self.control_session = control_session
        self.workspace_id = workspace_id

        self.repository = APIKeyAuditRepository(
            tenant_session,
            workspace_id,
        )

    def _payload(
        self,
        event: APIKeyAuditOutbox,
    ) -> dict:
        if event.workspace_id != self.workspace_id:
            raise APIKeyAuditDeliveryError(
                "Audit event workspace mismatch."
            )

        if event.action not in {"created", "revoked", "rotated"}:
            raise APIKeyAuditDeliveryError(
                "Unsupported API key audit action."
            )

        if (
            event.occurred_at.tzinfo is None
            or event.occurred_at.utcoffset() is None
        ):
            raise APIKeyAuditDeliveryError(
                "Audit event timestamp must include a timezone."
            )

        if event.action == "rotated":
            if (
                event.replacement_key_id is None
                or event.replacement_key_id == event.key_id
            ):
                raise APIKeyAuditDeliveryError(
                    "Invalid API key rotation audit event."
                )
        elif event.replacement_key_id is not None:
            raise APIKeyAuditDeliveryError(
                "Only rotation events may reference a replacement key."
            )

        event_data = {}

        if event.replacement_key_id is not None:
            event_data["replacement_key_id"] = str(
                event.replacement_key_id
            )

        return {
            "id": event.id,
            "workspace_id": event.workspace_id,
            "actor_user_id": event.actor_user_id,
            "category": "api_keys",
            "action": "api_keys." + event.action,
            "outcome": "success",
            "severity": "info",
            "target_type": "workspace_api_key",
            "target_id": event.key_id,
            "target_label": None,
            "message": None,
            "request_id": None,
            "ip_address": None,
            "user_agent": None,
            "event_data": event_data,
            "occurred_at": event.occurred_at.astimezone(
                timezone.utc
            ),
        }

    @staticmethod
    def _matches(
        existing: WorkspaceAuditEvent,
        payload: dict,
    ) -> bool:
        fields = (
            "workspace_id",
            "actor_user_id",
            "category",
            "action",
            "outcome",
            "severity",
            "target_type",
            "target_id",
            "target_label",
            "message",
            "request_id",
            "ip_address",
            "user_agent",
            "event_data",
            "occurred_at",
        )

        return all(
            getattr(existing, field) == payload[field]
            for field in fields
        )

    async def _write_control_event(
        self,
        event: APIKeyAuditOutbox,
    ) -> None:
        payload = self._payload(event)

        statement = (
            insert(WorkspaceAuditEvent)
            .values(**payload)
            .on_conflict_do_nothing(
                index_elements=[WorkspaceAuditEvent.id]
            )
        )

        await self.control_session.execute(statement)

        result = await self.control_session.execute(
            select(WorkspaceAuditEvent).where(
                WorkspaceAuditEvent.id == event.id
            )
        )

        existing = result.scalar_one()

        if not self._matches(existing, payload):
            raise APIKeyAuditDeliveryError(
                "Existing audit event does not match the outbox event."
            )

    async def deliver(
        self,
        *,
        limit: int = 100,
    ) -> int:
        try:
            events = await self.repository.pending(limit=limit)

            if not events:
                await self.tenant_session.rollback()
                await self.control_session.rollback()
                return 0

            for event in events:
                await self._write_control_event(event)

            # Control records become durable first.
            await self.control_session.commit()

            delivered_at = datetime.now(timezone.utc)

            for event in events:
                event.delivered_at = delivered_at

            await self.tenant_session.flush()
            await self.tenant_session.commit()

            return len(events)

        except BaseException:
            # Attempt both rollbacks without replacing the original error.
            for session in (
                self.control_session,
                self.tenant_session,
            ):
                try:
                    await session.rollback()
                except BaseException:
                    pass

            raise