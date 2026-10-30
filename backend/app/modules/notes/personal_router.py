from __future__ import annotations

import uuid

from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    Response,
    status,
)

from app.db.tenant_dependency import (
    ControlDB,
    VerifiedUser,
)
from app.modules.attachments.note_service import (
    list_note_attachments,
)
from app.modules.attachments.schemas import (
    AttachmentListResponse,
    AttachmentResponse,
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
from app.modules.notes.personal_service import (
    PersonalNoteNotFoundError,
    PersonalNoteService,
)


router = APIRouter(
    prefix="/notes",
    tags=["Personal notes"],
)


def note_not_found(
    exc: PersonalNoteNotFoundError,
) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=str(exc),
    )


@router.get(
    "/me",
    response_model=PersonalNoteListResponse,
)
async def list_my_notes(
    db: ControlDB,
    current_user: VerifiedUser,
    include_archived: bool = Query(default=False),
    search: str | None = Query(
        default=None,
        max_length=200,
    ),
    note_filter: PersonalNoteFilter = Query(
        default="all",
        alias="filter",
    ),
    sort: PersonalNoteSort = Query(default="updated"),
) -> PersonalNoteListResponse:
    return await PersonalNoteService(db).list_my_notes(
        current_user.id,
        include_archived,
        search=search,
        note_filter=note_filter,
        sort=sort,
    )


@router.post(
    "/me",
    response_model=PersonalNotePublic,
    status_code=status.HTTP_201_CREATED,
)
async def create_my_note(
    request: PersonalNoteCreateRequest,
    db: ControlDB,
    current_user: VerifiedUser,
) -> PersonalNotePublic:
    return await PersonalNoteService(db).create_my_note(
        current_user.id,
        request,
    )


@router.get(
    "/me/stats",
    response_model=PersonalNoteStatsResponse,
)
async def get_my_stats(
    db: ControlDB,
    current_user: VerifiedUser,
) -> PersonalNoteStatsResponse:
    return await PersonalNoteService(db).get_my_stats(
        current_user.id,
    )


@router.get(
    "/me/{note_id}/attachments",
    response_model=AttachmentListResponse,
)
async def get_my_note_attachments(
    note_id: uuid.UUID,
    db: ControlDB,
    current_user: VerifiedUser,
) -> AttachmentListResponse:
    attachments = await list_note_attachments(
        db,
        current_user.id,
        note_id,
    )

    return AttachmentListResponse(
        items=[
            AttachmentResponse.model_validate(attachment)
            for attachment in attachments
        ]
    )


@router.post(
    "/me/{note_id}/duplicate",
    response_model=PersonalNotePublic,
    status_code=status.HTTP_201_CREATED,
)
async def duplicate_my_note(
    note_id: uuid.UUID,
    db: ControlDB,
    current_user: VerifiedUser,
) -> PersonalNotePublic:
    try:
        return await PersonalNoteService(db).duplicate_my_note(
            current_user.id,
            note_id,
        )
    except PersonalNoteNotFoundError as exc:
        raise note_not_found(exc) from exc


@router.get(
    "/me/{note_id}",
    response_model=PersonalNotePublic,
)
async def get_my_note(
    note_id: uuid.UUID,
    db: ControlDB,
    current_user: VerifiedUser,
) -> PersonalNotePublic:
    try:
        return await PersonalNoteService(db).get_my_note(
            current_user.id,
            note_id,
        )
    except PersonalNoteNotFoundError as exc:
        raise note_not_found(exc) from exc


@router.patch(
    "/me/{note_id}",
    response_model=PersonalNotePublic,
)
async def update_my_note(
    note_id: uuid.UUID,
    request: PersonalNoteUpdateRequest,
    db: ControlDB,
    current_user: VerifiedUser,
) -> PersonalNotePublic:
    try:
        return await PersonalNoteService(db).update_my_note(
            current_user.id,
            note_id,
            request,
        )
    except PersonalNoteNotFoundError as exc:
        raise note_not_found(exc) from exc


@router.delete(
    "/me/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_my_note(
    note_id: uuid.UUID,
    db: ControlDB,
    current_user: VerifiedUser,
) -> Response:
    try:
        await PersonalNoteService(db).delete_my_note(
            current_user.id,
            note_id,
        )
    except PersonalNoteNotFoundError as exc:
        raise note_not_found(exc) from exc

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )


__all__ = ["router"]