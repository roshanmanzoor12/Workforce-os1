from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.api_keys.audit_models import APIKeyAuditOutbox


AUDIT_ACTIONS = frozenset({"created", "revoked", "rotated"})


class APIKeyAuditRepository:
    def __init__(
        self,
        session: AsyncSession,
        workspace_id: UUID,
    ) -> None:
        self.session = session
        self.workspace_id = workspace_id

    def enqueue(
        self,
        *,
        actor_user_id: UUID,
        key_id: UUID,
        action: str,
        occurred_at: datetime,
        replacement_key_id: UUID | None = None,
    ) -> APIKeyAuditOutbox:
        if action not in AUDIT_ACTIONS:
            raise ValueError("Unsupported API key audit action.")

        if (action == "rotated") != (replacement_key_id is not None):
            raise ValueError(
                "Only rotation events require a replacement key ID."
            )

        if replacement_key_id == key_id:
            raise ValueError(
                "A replacement key must differ from the original."
            )

        if (
            occurred_at.tzinfo is None
            or occurred_at.utcoffset() is None
        ):
            raise ValueError("Audit timestamps must be timezone-aware.")

        event = APIKeyAuditOutbox(
            id=uuid4(),
            workspace_id=self.workspace_id,
            actor_user_id=actor_user_id,
            key_id=key_id,
            action=action,
            replacement_key_id=replacement_key_id,
            occurred_at=occurred_at.astimezone(timezone.utc),
            delivered_at=None,
        )

        # No separate commit: the API key service owns the transaction.
        self.session.add(event)
        return event

    async def pending(
        self,
        *,
        limit: int = 100,
    ) -> list[APIKeyAuditOutbox]:
        if not 1 <= limit <= 1000:
            raise ValueError("Delivery batch size must be 1 through 1000.")

        result = await self.session.execute(
            select(APIKeyAuditOutbox)
            .where(
                APIKeyAuditOutbox.workspace_id == self.workspace_id,
                APIKeyAuditOutbox.delivered_at.is_(None),
            )
            .order_by(
                APIKeyAuditOutbox.occurred_at,
                APIKeyAuditOutbox.id,
            )
            .limit(limit)
            .with_for_update(skip_locked=True)
        )

        return list(result.scalars().all())