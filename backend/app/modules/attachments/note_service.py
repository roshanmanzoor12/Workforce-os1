from __future__ import annotations

import uuid

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.attachments.models import (
    Attachment,
    AttachmentScope,
    AttachmentStatus,
)
from app.modules.attachments.service import (
    AttachmentService,
)
from app.modules.attachments.storage import (
    get_attachment_storage,
)
from app.modules.notes.personal_models import (
    PersonalNote,
)


async def require_note(
    db: AsyncSession,
    user_id: uuid.UUID,
    note_id: uuid.UUID,
    *,
    lock: bool = False,
) -> PersonalNote:
    query = select(PersonalNote).where(
        PersonalNote.id == note_id,
        PersonalNote.owner_user_id == user_id,
    )

    if lock:
        query = query.with_for_update()

    note = (
        await db.execute(query)
    ).scalar_one_or_none()

    if note is None:
        raise HTTPException(
            404,
            "Note not found.",
        )

    return note


async def list_note_attachments(
    db: AsyncSession,
    user_id: uuid.UUID,
    note_id: uuid.UUID,
) -> list[Attachment]:
    await require_note(
        db,
        user_id,
        note_id,
    )

    query = (
        select(Attachment)
        .where(
            Attachment.scope == AttachmentScope.NOTE,
            Attachment.personal_note_id == note_id,
            Attachment.owner_user_id == user_id,
            Attachment.status == AttachmentStatus.READY,
        )
        .order_by(
            Attachment.created_at.asc(),
            Attachment.id.asc(),
        )
    )

    return list(
        (await db.execute(query)).scalars().all()
    )


async def delete_note_attachments(
    db: AsyncSession,
    user_id: uuid.UUID,
    note_id: uuid.UUID,
) -> None:
    # The calling Notes service owns the transaction
    # and must already hold the note lock.
    query = (
        select(Attachment)
        .where(
            Attachment.scope == AttachmentScope.NOTE,
            Attachment.personal_note_id == note_id,
        )
        .order_by(Attachment.id.asc())
        .with_for_update()
    )

    attachments = list(
        (await db.execute(query)).scalars().all()
    )

    if not attachments:
        return

    service = AttachmentService(
        db=db,
        storage=get_attachment_storage(),
    )

    for attachment in attachments:
        await service.delete(
            attachment_id=attachment.id,
            user_id=user_id,
            commit=False,
        )

        # Retain the deleted attachment metadata while releasing
        # its foreign key before the note itself is removed.
        attachment.personal_note_id = None

    await db.flush()