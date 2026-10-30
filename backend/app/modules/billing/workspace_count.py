from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.workspaces.models import (
    WORKSPACE_STATUS_ARCHIVED,
    Workspace,
)


async def count_owned_active_workspaces(
    session: AsyncSession,
    user_id: uuid.UUID,
) -> int:
    statement = (
        select(
            func.count(
                Workspace.id
            )
        )
        .where(
            Workspace.created_by_user_id
            == user_id,
        )
        .where(
            Workspace.is_active.is_(
                True
            )
        )
        .where(
            Workspace.status
            != WORKSPACE_STATUS_ARCHIVED
        )
    )

    result = await session.execute(
        statement
    )

    return int(
        result.scalar_one()
    )