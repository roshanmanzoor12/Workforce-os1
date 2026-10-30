from __future__ import annotations

import logging
import uuid

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.modules.audit_log.schemas import (
    AuditEventCreate,
)
from app.modules.audit_log.service import (
    AuditLogService,
)
from app.modules.shifts.events import (
    SCHEDULE_PUBLISHED_EVENT,
)
from app.modules.shifts.models import (
    SchedulePublication,
)


logger = logging.getLogger(
    __name__
)


async def audit_schedule_published(
    *,
    control_session: AsyncSession,
    workspace_id: uuid.UUID,
    actor_user_id: uuid.UUID,
    publication: SchedulePublication,
) -> None:
    """
    Append the control-plane audit event.

    Tenant and control databases cannot share one SQL
    transaction, so an audit storage failure must not roll
    back an already-committed tenant publication.
    """

    try:
        await AuditLogService(
            control_session
        ).record(
            workspace_id=workspace_id,
            payload=AuditEventCreate(
                actor_user_id=(
                    actor_user_id
                ),
                category="scheduling",
                action=(
                    SCHEDULE_PUBLISHED_EVENT
                ),
                target_type=(
                    "schedule_publication"
                ),
                target_id=(
                    publication.id
                ),
                target_label=(
                    "Published schedule"
                ),
                event_data={
                    "period_start": (
                        publication
                        .period_start
                        .isoformat()
                    ),
                    "period_end": (
                        publication
                        .period_end
                        .isoformat()
                    ),
                },
            ),
        )

        await control_session.commit()

    except Exception:
        await control_session.rollback()

        logger.exception(
            "Unable to persist schedule "
            "publication audit event."
        )


__all__ = [
    "audit_schedule_published",
]