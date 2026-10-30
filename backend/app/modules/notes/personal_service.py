from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.attachments.note_service import (
    delete_note_attachments,
)
from app.modules.notes.personal_document import (
    PersonalNoteDocument,
    read_personal_document,
)
from app.modules.notes.personal_models import (
    PersonalNote,
)
from app.modules.notes.personal_schemas import (
    PersonalNoteCreateRequest,
    PersonalNoteFilter,
    PersonalNoteListResponse,
    PersonalNotePublic,
    PersonalNoteSort,
    PersonalNoteStatsResponse,
    PersonalNoteUpdateRequest,
)


class PersonalNoteNotFoundError(LookupError):
    pass


class PersonalNoteService:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    @staticmethod
    def _document(
        note: PersonalNote,
    ) -> PersonalNoteDocument:
        try:
            return read_personal_document(note.content)
        except ValueError:
            return PersonalNoteDocument(
                content_format="plain",
                plain_text=note.content,
                tags=(),
                checklist_total=0,
                checklist_completed=0,
            )

    @classmethod
    def _public(
        cls,
        note: PersonalNote,
    ) -> PersonalNotePublic:
        document = cls._document(note)

        return PersonalNotePublic(
            id=note.id,
            owner_user_id=note.owner_user_id,
            title=note.title,
            content=note.content,
            is_pinned=note.is_pinned,
            is_archived=note.is_archived,
            created_at=note.created_at,
            updated_at=note.updated_at,
            content_format=document.content_format,
            plain_text=document.plain_text,
            tags=list(document.tags),
            checklist_total=document.checklist_total,
            checklist_completed=document.checklist_completed,
        )

    async def list_my_notes(
        self,
        owner_user_id: uuid.UUID,
        include_archived: bool = False,
        *,
        search: str | None = None,
        note_filter: PersonalNoteFilter = "all",
        sort: PersonalNoteSort = "updated",
    ) -> PersonalNoteListResponse:
        statement = select(PersonalNote).where(
            PersonalNote.owner_user_id == owner_user_id,
        )

        if note_filter == "archived":
            statement = statement.where(
                PersonalNote.is_archived.is_(True),
            )
        elif not include_archived:
            statement = statement.where(
                PersonalNote.is_archived.is_(False),
            )

        if note_filter == "pinned":
            statement = statement.where(
                PersonalNote.is_pinned.is_(True),
            )

        if sort == "created":
            ordering = PersonalNote.created_at.desc()
        elif sort == "oldest":
            ordering = PersonalNote.updated_at.asc()
        elif sort == "title":
            ordering = func.lower(PersonalNote.title).asc()
        else:
            ordering = PersonalNote.updated_at.desc()

        statement = statement.order_by(
            PersonalNote.is_pinned.desc(),
            ordering,
            PersonalNote.id.desc(),
        )

        result = await self.session.execute(statement)

        query = (search or "").strip().casefold()
        items: list[PersonalNotePublic] = []

        for note in result.scalars().all():
            public = self._public(note)

            if (
                note_filter == "checklists"
                and public.checklist_total == 0
            ):
                continue

            if query:
                searchable = "\n".join(
                    [
                        public.title,
                        public.plain_text,
                        *public.tags,
                    ]
                ).casefold()

                if query not in searchable:
                    continue

            items.append(public)

        return PersonalNoteListResponse(
            items=items,
            total=len(items),
        )

    async def get_my_stats(
        self,
        owner_user_id: uuid.UUID,
    ) -> PersonalNoteStatsResponse:
        statement = select(
            func.count(PersonalNote.id),
            func.count(PersonalNote.id).filter(
                PersonalNote.is_pinned.is_(True),
            ),
            func.count(PersonalNote.id).filter(
                PersonalNote.is_archived.is_(True),
            ),
        ).where(
            PersonalNote.owner_user_id == owner_user_id,
        )

        total, pinned, archived = (
            await self.session.execute(statement)
        ).one()

        return PersonalNoteStatsResponse(
            total=int(total),
            pinned=int(pinned),
            archived=int(archived),
        )

    async def create_my_note(
        self,
        owner_user_id: uuid.UUID,
        request: PersonalNoteCreateRequest,
    ) -> PersonalNotePublic:
        note = PersonalNote(
            owner_user_id=owner_user_id,
            title=request.title,
            content=request.content,
            is_pinned=False,
            is_archived=False,
        )

        try:
            self.session.add(note)
            await self.session.flush()
            await self.session.commit()
            await self.session.refresh(note)

            return self._public(note)
        except Exception:
            await self.session.rollback()
            raise

    async def get_my_note(
        self,
        owner_user_id: uuid.UUID,
        note_id: uuid.UUID,
    ) -> PersonalNotePublic:
        note = await self._require_owned_note(
            owner_user_id,
            note_id,
        )

        return self._public(note)

    async def update_my_note(
        self,
        owner_user_id: uuid.UUID,
        note_id: uuid.UUID,
        request: PersonalNoteUpdateRequest,
    ) -> PersonalNotePublic:
        try:
            note = await self._require_owned_note(
                owner_user_id,
                note_id,
                lock=True,
            )

            values = request.model_dump(
                exclude_unset=True,
            )

            for field, value in values.items():
                setattr(note, field, value)

            await self.session.flush()
            await self.session.commit()
            await self.session.refresh(note)

            return self._public(note)
        except Exception:
            await self.session.rollback()
            raise

    async def duplicate_my_note(
        self,
        owner_user_id: uuid.UUID,
        note_id: uuid.UUID,
    ) -> PersonalNotePublic:
        try:
            source = await self._require_owned_note(
                owner_user_id,
                note_id,
                lock=True,
            )

            suffix = " (copy)"

            duplicate = PersonalNote(
                owner_user_id=owner_user_id,
                title=(
                    source.title[:200 - len(suffix)].rstrip()
                    + suffix
                ),
                content=source.content,
                is_pinned=False,
                is_archived=False,
            )

            # This duplicates the document, not its uploaded files.
            self.session.add(duplicate)

            await self.session.flush()
            await self.session.commit()
            await self.session.refresh(duplicate)

            return self._public(duplicate)
        except Exception:
            await self.session.rollback()
            raise

    async def delete_my_note(
        self,
        owner_user_id: uuid.UUID,
        note_id: uuid.UUID,
    ) -> None:
        try:
            note = await self._require_owned_note(
                owner_user_id,
                note_id,
                lock=True,
            )

            await delete_note_attachments(
                self.session,
                owner_user_id,
                note_id,
            )

            await self.session.delete(note)
            await self.session.flush()
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

    async def _require_owned_note(
        self,
        owner_user_id: uuid.UUID,
        note_id: uuid.UUID,
        *,
        lock: bool = False,
    ) -> PersonalNote:
        statement = select(PersonalNote).where(
            PersonalNote.id == note_id,
            PersonalNote.owner_user_id == owner_user_id,
        )

        if lock:
            statement = statement.with_for_update()

        note = (
            await self.session.execute(statement)
        ).scalar_one_or_none()

        if note is None:
            raise PersonalNoteNotFoundError(
                "Note not found."
            )

        return note


__all__ = [
    "PersonalNoteService",
    "PersonalNoteNotFoundError",
]