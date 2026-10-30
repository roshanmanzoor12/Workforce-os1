from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.api_keys.models import WorkspaceAPIKey


class APIKeyRepository:
    def __init__(
        self,
        session: AsyncSession,
        workspace_id: UUID,
    ) -> None:
        self.session = session
        self.workspace_id = workspace_id

    async def list(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[WorkspaceAPIKey]:
        result = await self.session.execute(
            select(WorkspaceAPIKey)
            .where(
                WorkspaceAPIKey.workspace_id == self.workspace_id
            )
            .order_by(
                WorkspaceAPIKey.created_at.desc(),
                WorkspaceAPIKey.id.desc(),
            )
            .limit(limit)
            .offset(offset)
        )

        return list(result.scalars().all())

    async def get(
        self,
        key_id: UUID,
        *,
        for_update: bool = False,
    ) -> WorkspaceAPIKey | None:
        statement = select(WorkspaceAPIKey).where(
            WorkspaceAPIKey.id == key_id,
            WorkspaceAPIKey.workspace_id == self.workspace_id,
        )

        if for_update:
            statement = statement.with_for_update()

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def add(self, key: WorkspaceAPIKey) -> None:
        if key.workspace_id != self.workspace_id:
            raise ValueError("API key workspace mismatch.")

        self.session.add(key)
        await self.session.flush()