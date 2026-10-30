from __future__ import annotations

import uuid

from sqlalchemy import (
    or_,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.knowledge.enums import (
    KnowledgeVisibility,
)
from app.modules.knowledge.models import (
    KnowledgeEntry,
)


class KnowledgeRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def create(
        self,
        entry: KnowledgeEntry,
    ) -> KnowledgeEntry:
        self.session.add(
            entry
        )

        await self.session.flush()

        return entry

    async def get_by_id(
        self,
        entry_id: uuid.UUID,
    ) -> KnowledgeEntry | None:
        result = await self.session.execute(
            select(
                KnowledgeEntry
            ).where(
                KnowledgeEntry.id
                == entry_id
            )
        )

        return result.scalar_one_or_none()

    async def list_for_employee(
        self,
        employee_id: uuid.UUID,
        include_archived: bool = False,
    ) -> list[KnowledgeEntry]:
        statement = select(
            KnowledgeEntry
        ).where(
            KnowledgeEntry.owner_employee_id
            == employee_id
        )

        if not include_archived:
            statement = statement.where(
                KnowledgeEntry.status
                != "archived"
            )

        statement = statement.order_by(
            KnowledgeEntry.updated_at.desc()
        )

        result = await self.session.execute(
            statement
        )

        return list(
            result.scalars().all()
        )

    async def list_workspace_visible(
        self,
        employee_id: uuid.UUID,
    ) -> list[KnowledgeEntry]:
        result = await self.session.execute(
            select(
                KnowledgeEntry
            )
            .where(
                or_(
                    KnowledgeEntry.owner_employee_id
                    == employee_id,
                    KnowledgeEntry.visibility
                    == (
                        KnowledgeVisibility
                        .WORKSPACE
                        .value
                    ),
                )
            )
            .order_by(
                KnowledgeEntry.updated_at.desc()
            )
        )

        return list(
            result.scalars().all()
        )

    async def delete(
        self,
        entry: KnowledgeEntry,
    ) -> None:
        await self.session.delete(
            entry
        )

        await self.session.flush()


__all__ = [
    "KnowledgeRepository",
]