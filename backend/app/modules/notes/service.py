from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.employees.repository import (
    EmployeeRepository,
)
from app.modules.notes.models import Note
from app.modules.notes.repository import (
    NoteRepository,
)
from app.modules.notes.schemas import (
    NoteCreateRequest,
    NoteListResponse,
    NotePublic,
    NoteUpdateRequest,
)


class NoteNotFoundError(
    LookupError
):
    pass


class NoteValidationError(
    ValueError
):
    pass


class NoteService:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

        self.repository = (
            NoteRepository(
                session
            )
        )

        self.employees = (
            EmployeeRepository(
                session
            )
        )

    async def create_note(
        self,
        request: NoteCreateRequest,
    ) -> NotePublic:
        employee = await (
            self.employees
            .get_employee_by_id(
                request.owner_employee_id
            )
        )

        if employee is None:
            raise NoteValidationError(
                "Employee not found."
            )

        if not employee.is_active:
            raise NoteValidationError(
                "Employee is not active."
            )

        note = Note(
            owner_employee_id=(
                request.owner_employee_id
            ),
            title=request.title,
            content=request.content,
            is_pinned=False,
            is_archived=False,
        )

        try:
            await self.repository.create(
                note
            )

            await self.session.commit()

            await self.session.refresh(
                note
            )
        except Exception:
            await self.session.rollback()
            raise

        return self._to_public(
            note
        )

    async def get_note(
        self,
        note_id: uuid.UUID,
    ) -> NotePublic:
        note = await self._require_note(
            note_id
        )

        return self._to_public(
            note
        )

    async def list_employee_notes(
        self,
        employee_id: uuid.UUID,
        include_archived: bool = False,
    ) -> NoteListResponse:
        notes = await (
            self.repository
            .list_for_employee(
                employee_id,
                include_archived,
            )
        )

        items = [
            self._to_public(
                note
            )
            for note in notes
        ]

        return NoteListResponse(
            items=items,
            total=len(items),
        )

    async def update_note(
        self,
        note_id: uuid.UUID,
        request: NoteUpdateRequest,
    ) -> NotePublic:
        note = await self._require_note(
            note_id
        )

        values = request.model_dump(
            exclude_unset=True
        )

        for key, value in values.items():
            setattr(
                note,
                key,
                value,
            )

        try:
            await self.session.commit()

            await self.session.refresh(
                note
            )
        except Exception:
            await self.session.rollback()
            raise

        return self._to_public(
            note
        )

    async def delete_note(
        self,
        note_id: uuid.UUID,
    ) -> None:
        note = await self._require_note(
            note_id
        )

        try:
            await self.repository.delete(
                note
            )

            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

    async def _require_note(
        self,
        note_id: uuid.UUID,
    ) -> Note:
        note = await (
            self.repository
            .get_by_id(
                note_id
            )
        )

        if note is None:
            raise NoteNotFoundError(
                "Note not found."
            )

        return note

    @staticmethod
    def _to_public(
        note: Note,
    ) -> NotePublic:
        return NotePublic.model_validate(
            note
        )


__all__ = [
    "NoteService",
    "NoteNotFoundError",
    "NoteValidationError",
]