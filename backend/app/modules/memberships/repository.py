from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.modules.memberships.models import (
    WorkspaceMembership,
)
from app.modules.workspaces.models import (
    MEMBERSHIP_STATUS_ACTIVE,
    MEMBERSHIP_STATUS_REMOVED,
)


class WorkspaceMembershipRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def get_by_id(
        self,
        membership_id: uuid.UUID,
    ) -> WorkspaceMembership | None:
        result = await self.session.execute(
            select(
                WorkspaceMembership
            ).where(
                WorkspaceMembership.id
                == membership_id
            )
        )

        return result.scalar_one_or_none()

    async def get_for_user(
        self,
        *,
        workspace_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> WorkspaceMembership | None:
        result = await self.session.execute(
            select(
                WorkspaceMembership
            ).where(
                WorkspaceMembership.workspace_id
                == workspace_id,
                WorkspaceMembership.user_id
                == user_id,
            )
        )

        return result.scalar_one_or_none()

    async def get_active_for_user(
        self,
        *,
        workspace_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> WorkspaceMembership | None:
        result = await self.session.execute(
            select(
                WorkspaceMembership
            ).where(
                WorkspaceMembership.workspace_id
                == workspace_id,
                WorkspaceMembership.user_id
                == user_id,
                WorkspaceMembership.status
                == MEMBERSHIP_STATUS_ACTIVE,
            )
        )

        return result.scalar_one_or_none()

    async def list_for_workspace(
        self,
        *,
        workspace_id: uuid.UUID,
        include_removed: bool = False,
    ) -> list[
        WorkspaceMembership
    ]:
        statement = (
            select(
                WorkspaceMembership
            )
            .where(
                WorkspaceMembership.workspace_id
                == workspace_id
            )
            .order_by(
                WorkspaceMembership.created_at
                .asc()
            )
        )

        if not include_removed:
            statement = statement.where(
                WorkspaceMembership.status
                != MEMBERSHIP_STATUS_REMOVED
            )

        result = await self.session.execute(
            statement
        )

        return list(
            result.scalars().all()
        )

    async def add(
        self,
        membership: WorkspaceMembership,
    ) -> None:
        self.session.add(
            membership
        )