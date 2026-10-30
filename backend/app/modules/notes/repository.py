from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.notes.models import Note


class NoteRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def create(
        self,
        note: Note,
    ) -> Note:
        self.session.add(
            note
        )

        await self.session.flush()

        return note

    async def get_by_id(
        self,
        note_id: uuid.UUID,
    ) -> Note | None:
        result = await self.session.execute(
            select(
                Note
            ).where(
                Note.id == note_id
            )
        )

        return result.scalar_one_or_none()

    async def list_for_employee(
        self,
        employee_id: uuid.UUID,
        include_archived: bool = False,
    ) -> list[Note]:
        statement = select(
            Note
        ).where(
            Note.owner_employee_id
            == employee_id
        )

        if not include_archived:
            statement = statement.where(
                Note.is_archived.is_(
                    False
                )
            )

        statement = statement.order_by(
            Note.is_pinned.desc(),
            Note.updated_at.desc(),
        )

        result = await self.session.execute(
            statement
        )

        return list(
            result.scalars().all()
        )

    async def delete(
        self,
        note: Note,
    ) -> None:
        await self.session.delete(
            note
        )

        await self.session.flush()


__all__ = [
    "NoteRepository",
]