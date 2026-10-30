from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    func,
    select,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.modules.audit_log.models import (
    WorkspaceAuditEvent,
)


class AuditLogRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    # =====================================================
    # INSERT
    # =====================================================

    async def create(
        self,
        event: WorkspaceAuditEvent,
    ) -> WorkspaceAuditEvent:
        self.session.add(
            event
        )

        await self.session.flush()

        await self.session.refresh(
            event
        )

        return event

    # =====================================================
    # READ ONE
    # =====================================================

    async def get(
        self,
        *,
        workspace_id: uuid.UUID,
        event_id: uuid.UUID,
    ) -> WorkspaceAuditEvent | None:
        result = await self.session.execute(
            select(
                WorkspaceAuditEvent
            ).where(
                WorkspaceAuditEvent.workspace_id
                == workspace_id,

                WorkspaceAuditEvent.id
                == event_id,
            )
        )

        return (
            result
            .scalar_one_or_none()
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
    ) -> tuple[
        list[WorkspaceAuditEvent],
        int,
    ]:
        filters = [
            WorkspaceAuditEvent.workspace_id
            == workspace_id
        ]

        if category:
            filters.append(
                WorkspaceAuditEvent.category
                == category
            )

        if action:
            filters.append(
                WorkspaceAuditEvent.action
                == action
            )

        if actor_user_id is not None:
            filters.append(
                WorkspaceAuditEvent.actor_user_id
                == actor_user_id
            )

        if target_type:
            filters.append(
                WorkspaceAuditEvent.target_type
                == target_type
            )

        if target_id is not None:
            filters.append(
                WorkspaceAuditEvent.target_id
                == target_id
            )

        if outcome:
            filters.append(
                WorkspaceAuditEvent.outcome
                == outcome
            )

        if severity:
            filters.append(
                WorkspaceAuditEvent.severity
                == severity
            )

        if start_at is not None:
            filters.append(
                WorkspaceAuditEvent.occurred_at
                >= start_at
            )

        if end_at is not None:
            filters.append(
                WorkspaceAuditEvent.occurred_at
                < end_at
            )

        count_result = (
            await self.session.execute(
                select(
                    func.count(
                        WorkspaceAuditEvent.id
                    )
                ).where(
                    *filters
                )
            )
        )

        total = int(
            count_result.scalar_one()
            or 0
        )

        result = await self.session.execute(
            select(
                WorkspaceAuditEvent
            )
            .where(
                *filters
            )
            .order_by(
                WorkspaceAuditEvent
                .occurred_at
                .desc(),

                WorkspaceAuditEvent
                .id
                .desc(),
            )
            .limit(
                limit
            )
            .offset(
                offset
            )
        )

        return (
            list(
                result
                .scalars()
                .all()
            ),
            total,
        )


__all__ = [
    "AuditLogRepository",
]