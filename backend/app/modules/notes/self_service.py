from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.employees.models import (
    Employee,
)
from app.modules.notes.schemas import (
    NoteCreateRequest,
    NoteListResponse,
    NotePublic,
    NoteUpdateRequest,
)
from app.modules.notes.service import (
    NoteNotFoundError,
    NoteService,
    NoteValidationError,
)


class NoteActorEmployeeNotFoundError(
    LookupError
):
    pass


class NoteSelfService:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

        self.notes = NoteService(
            session
        )

    async def resolve_actor_employee(
        self,
        actor_user_id: uuid.UUID,
    ) -> Employee:
        result = await self.session.execute(
            select(
                Employee
            ).where(
                Employee.user_id
                == actor_user_id,
                Employee.is_active.is_(
                    True
                ),
            )
        )

        employee = (
            result.scalar_one_or_none()
        )

        if employee is None:
            raise (
                NoteActorEmployeeNotFoundError(
                    "Active employee profile "
                    "for current user was "
                    "not found."
                )
            )

        return employee

    async def create_my_note(
        self,
        actor_user_id: uuid.UUID,
        request: NoteCreateRequest,
    ) -> NotePublic:
        employee = await (
            self.resolve_actor_employee(
                actor_user_id
            )
        )

        trusted_request = (
            NoteCreateRequest(
                owner_employee_id=(
                    employee.id
                ),
                title=request.title,
                content=request.content,
            )
        )

        return await (
            self.notes.create_note(
                trusted_request
            )
        )

    async def list_my_notes(
        self,
        actor_user_id: uuid.UUID,
        include_archived: bool = False,
    ) -> NoteListResponse:
        employee = await (
            self.resolve_actor_employee(
                actor_user_id
            )
        )

        return await (
            self.notes
            .list_employee_notes(
                employee.id,
                include_archived,
            )
        )

    async def get_my_note(
        self,
        actor_user_id: uuid.UUID,
        note_id: uuid.UUID,
    ) -> NotePublic:
        employee = await (
            self.resolve_actor_employee(
                actor_user_id
            )
        )

        note = await (
            self.notes.get_note(
                note_id
            )
        )

        if (
            note.owner_employee_id
            != employee.id
        ):
            raise NoteNotFoundError(
                "Note not found."
            )

        return note

    async def update_my_note(
        self,
        actor_user_id: uuid.UUID,
        note_id: uuid.UUID,
        request: NoteUpdateRequest,
    ) -> NotePublic:
        await self.get_my_note(
            actor_user_id,
            note_id,
        )

        return await (
            self.notes.update_note(
                note_id,
                request,
            )
        )

    async def delete_my_note(
        self,
        actor_user_id: uuid.UUID,
        note_id: uuid.UUID,
    ) -> None:
        await self.get_my_note(
            actor_user_id,
            note_id,
        )

        await self.notes.delete_note(
            note_id
        )


__all__ = [
    "NoteSelfService",
    "NoteActorEmployeeNotFoundError",
    "NoteNotFoundError",
    "NoteValidationError",
]