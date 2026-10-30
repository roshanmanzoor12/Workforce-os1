from __future__ import annotations

import uuid

from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    status,
)

from app.db.tenant_dependency import (
    TenantScope,
)
from app.modules.meetings.router import (
    actor_user_id_from_scope,
)
from app.modules.notes.schemas import (
    NoteCreateRequest,
    NoteListResponse,
    NotePublic,
    NoteUpdateRequest,
)
from app.modules.notes.self_service import (
    NoteActorEmployeeNotFoundError,
    NoteSelfService,
)
from app.modules.notes.service import (
    NoteNotFoundError,
    NoteService,
    NoteValidationError,
)
from app.modules.workspace_permissions.permissions import (
    WorkspacePermission,
)
from app.modules.workspace_permissions.service import (
    WorkspacePermissionService,
)


router = APIRouter(
    prefix=(
        "/workspaces/"
        "{workspace_id}/notes"
    ),
    tags=[
        "notes",
    ],
)


def permissions(
    scope: TenantScope,
) -> WorkspacePermissionService:
    return WorkspacePermissionService(
        scope
    )


def raise_note_error(
    exc: Exception,
) -> None:
    if isinstance(
        exc,
        (
            NoteNotFoundError,
            NoteActorEmployeeNotFoundError,
        ),
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=str(exc),
        ) from exc

    if isinstance(
        exc,
        NoteValidationError,
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail=str(exc),
        ) from exc

    raise exc


@router.get(
    "/me",
    response_model=NoteListResponse,
)
async def list_my_notes(
    scope: TenantScope,
    include_archived: bool = Query(
        default=False,
    ),
) -> NoteListResponse:
    permissions(
        scope
    ).require(
        WorkspacePermission
        .NOTES_SELF
        .value
    )

    try:
        return await NoteSelfService(
            scope.session
        ).list_my_notes(
            actor_user_id_from_scope(
                scope
            ),
            include_archived,
        )
    except Exception as exc:
        raise_note_error(
            exc
        )
        raise


@router.post(
    "/me",
    response_model=NotePublic,
    status_code=(
        status.HTTP_201_CREATED
    ),
)
async def create_my_note(
    request: NoteCreateRequest,
    scope: TenantScope,
) -> NotePublic:
    permissions(
        scope
    ).require(
        WorkspacePermission
        .NOTES_SELF
        .value
    )

    try:
        return await NoteSelfService(
            scope.session
        ).create_my_note(
            actor_user_id_from_scope(
                scope
            ),
            request,
        )
    except Exception as exc:
        raise_note_error(
            exc
        )
        raise


@router.get(
    "/me/{note_id}",
    response_model=NotePublic,
)
async def get_my_note(
    note_id: uuid.UUID,
    scope: TenantScope,
) -> NotePublic:
    permissions(
        scope
    ).require(
        WorkspacePermission
        .NOTES_SELF
        .value
    )

    try:
        return await NoteSelfService(
            scope.session
        ).get_my_note(
            actor_user_id_from_scope(
                scope
            ),
            note_id,
        )
    except Exception as exc:
        raise_note_error(
            exc
        )
        raise


@router.patch(
    "/me/{note_id}",
    response_model=NotePublic,
)
async def update_my_note(
    note_id: uuid.UUID,
    request: NoteUpdateRequest,
    scope: TenantScope,
) -> NotePublic:
    permissions(
        scope
    ).require(
        WorkspacePermission
        .NOTES_SELF
        .value
    )

    try:
        return await NoteSelfService(
            scope.session
        ).update_my_note(
            actor_user_id_from_scope(
                scope
            ),
            note_id,
            request,
        )
    except Exception as exc:
        raise_note_error(
            exc
        )
        raise


@router.delete(
    "/me/{note_id}",
    status_code=(
        status.HTTP_204_NO_CONTENT
    ),
)
async def delete_my_note(
    note_id: uuid.UUID,
    scope: TenantScope,
) -> None:
    permissions(
        scope
    ).require(
        WorkspacePermission
        .NOTES_SELF
        .value
    )

    try:
        await NoteSelfService(
            scope.session
        ).delete_my_note(
            actor_user_id_from_scope(
                scope
            ),
            note_id,
        )
    except Exception as exc:
        raise_note_error(
            exc
        )


@router.get(
    "/employee/{employee_id}",
    response_model=NoteListResponse,
)
async def list_employee_notes(
    employee_id: uuid.UUID,
    scope: TenantScope,
    include_archived: bool = Query(
        default=False,
    ),
) -> NoteListResponse:
    permissions(
        scope
    ).require(
        WorkspacePermission
        .NOTES_VIEW
        .value
    )

    return await NoteService(
        scope.session
    ).list_employee_notes(
        employee_id,
        include_archived,
    )


@router.get(
    "/{note_id}",
    response_model=NotePublic,
)
async def get_note(
    note_id: uuid.UUID,
    scope: TenantScope,
) -> NotePublic:
    permissions(
        scope
    ).require(
        WorkspacePermission
        .NOTES_VIEW
        .value
    )

    try:
        return await NoteService(
            scope.session
        ).get_note(
            note_id
        )
    except Exception as exc:
        raise_note_error(
            exc
        )
        raise


@router.patch(
    "/{note_id}",
    response_model=NotePublic,
)
async def update_note(
    note_id: uuid.UUID,
    request: NoteUpdateRequest,
    scope: TenantScope,
) -> NotePublic:
    permissions(
        scope
    ).require(
        WorkspacePermission
        .NOTES_MANAGE
        .value
    )

    try:
        return await NoteService(
            scope.session
        ).update_note(
            note_id,
            request,
        )
    except Exception as exc:
        raise_note_error(
            exc
        )
        raise


@router.delete(
    "/{note_id}",
    status_code=(
        status.HTTP_204_NO_CONTENT
    ),
)
async def delete_note(
    note_id: uuid.UUID,
    scope: TenantScope,
) -> None:
    permissions(
        scope
    ).require(
        WorkspacePermission
        .NOTES_MANAGE
        .value
    )

    try:
        await NoteService(
            scope.session
        ).delete_note(
            note_id
        )
    except Exception as exc:
        raise_note_error(
            exc
        )