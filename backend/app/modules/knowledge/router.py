from __future__ import annotations

import uuid

from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    status,
)

from app.db.tenant_dependency import TenantScope
from app.modules.knowledge.schemas import (
    KnowledgeCreateRequest,
    KnowledgeListResponse,
    KnowledgePublic,
    KnowledgeUpdateRequest,
)
from app.modules.knowledge.service import (
    KnowledgeActorEmployeeNotFoundError,
    KnowledgeNotFoundError,
    KnowledgeService,
    KnowledgeValidationError,
)
from app.modules.meetings.router import (
    actor_user_id_from_scope,
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
        "{workspace_id}/knowledge"
    ),
    tags=[
        "knowledge",
    ],
)


def permissions(
    scope: TenantScope,
) -> WorkspacePermissionService:
    return WorkspacePermissionService(
        scope
    )


def service(
    scope: TenantScope,
) -> KnowledgeService:
    return KnowledgeService(
        scope.session
    )


def raise_knowledge_error(
    exc: Exception,
) -> None:
    if isinstance(
        exc,
        (
            KnowledgeNotFoundError,
            KnowledgeActorEmployeeNotFoundError,
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
        KnowledgeValidationError,
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
    response_model=KnowledgeListResponse,
)
async def list_my_knowledge(
    scope: TenantScope,
    include_archived: bool = Query(
        default=False,
    ),
) -> KnowledgeListResponse:
    permissions(
        scope
    ).require(
        WorkspacePermission
        .KNOWLEDGE_SELF
        .value
    )

    try:
        return await service(
            scope
        ).list_my_entries(
            actor_user_id_from_scope(
                scope
            ),
            include_archived,
        )
    except Exception as exc:
        raise_knowledge_error(
            exc
        )
        raise


@router.post(
    "/me",
    response_model=KnowledgePublic,
    status_code=(
        status.HTTP_201_CREATED
    ),
)
async def create_my_knowledge(
    request: KnowledgeCreateRequest,
    scope: TenantScope,
) -> KnowledgePublic:
    permissions(
        scope
    ).require(
        WorkspacePermission
        .KNOWLEDGE_SELF
        .value
    )

    try:
        return await service(
            scope
        ).create_my_entry(
            actor_user_id_from_scope(
                scope
            ),
            request,
        )
    except Exception as exc:
        raise_knowledge_error(
            exc
        )
        raise


@router.get(
    "/me/{entry_id}",
    response_model=KnowledgePublic,
)
async def get_my_knowledge(
    entry_id: uuid.UUID,
    scope: TenantScope,
) -> KnowledgePublic:
    permissions(
        scope
    ).require(
        WorkspacePermission
        .KNOWLEDGE_SELF
        .value
    )

    try:
        return await service(
            scope
        ).get_my_entry(
            actor_user_id_from_scope(
                scope
            ),
            entry_id,
        )
    except Exception as exc:
        raise_knowledge_error(
            exc
        )
        raise


@router.patch(
    "/me/{entry_id}",
    response_model=KnowledgePublic,
)
async def update_my_knowledge(
    entry_id: uuid.UUID,
    request: KnowledgeUpdateRequest,
    scope: TenantScope,
) -> KnowledgePublic:
    permissions(
        scope
    ).require(
        WorkspacePermission
        .KNOWLEDGE_SELF
        .value
    )

    try:
        return await service(
            scope
        ).update_my_entry(
            actor_user_id_from_scope(
                scope
            ),
            entry_id,
            request,
        )
    except Exception as exc:
        raise_knowledge_error(
            exc
        )
        raise


@router.delete(
    "/me/{entry_id}",
    status_code=(
        status.HTTP_204_NO_CONTENT
    ),
)
async def delete_my_knowledge(
    entry_id: uuid.UUID,
    scope: TenantScope,
) -> None:
    permissions(
        scope
    ).require(
        WorkspacePermission
        .KNOWLEDGE_SELF
        .value
    )

    try:
        await service(
            scope
        ).delete_my_entry(
            actor_user_id_from_scope(
                scope
            ),
            entry_id,
        )
    except Exception as exc:
        raise_knowledge_error(
            exc
        )


@router.get(
    "/workspace",
    response_model=KnowledgeListResponse,
)
async def list_workspace_knowledge(
    scope: TenantScope,
) -> KnowledgeListResponse:
    permissions(
        scope
    ).require(
        WorkspacePermission
        .KNOWLEDGE_VIEW
        .value
    )

    try:
        return await service(
            scope
        ).list_workspace_entries(
            actor_user_id_from_scope(
                scope
            )
        )
    except Exception as exc:
        raise_knowledge_error(
            exc
        )
        raise


@router.get(
    "/{entry_id}",
    response_model=KnowledgePublic,
)
async def get_knowledge(
    entry_id: uuid.UUID,
    scope: TenantScope,
) -> KnowledgePublic:
    permissions(
        scope
    ).require(
        WorkspacePermission
        .KNOWLEDGE_VIEW
        .value
    )

    try:
        return await service(
            scope
        ).get_entry(
            entry_id
        )
    except Exception as exc:
        raise_knowledge_error(
            exc
        )
        raise


@router.patch(
    "/{entry_id}",
    response_model=KnowledgePublic,
)
async def update_knowledge(
    entry_id: uuid.UUID,
    request: KnowledgeUpdateRequest,
    scope: TenantScope,
) -> KnowledgePublic:
    permissions(
        scope
    ).require(
        WorkspacePermission
        .KNOWLEDGE_MANAGE
        .value
    )

    try:
        return await service(
            scope
        ).update_entry(
            entry_id,
            request,
        )
    except Exception as exc:
        raise_knowledge_error(
            exc
        )
        raise


@router.delete(
    "/{entry_id}",
    status_code=(
        status.HTTP_204_NO_CONTENT
    ),
)
async def delete_knowledge(
    entry_id: uuid.UUID,
    scope: TenantScope,
) -> None:
    permissions(
        scope
    ).require(
        WorkspacePermission
        .KNOWLEDGE_MANAGE
        .value
    )

    try:
        await service(
            scope
        ).delete_entry(
            entry_id
        )
    except Exception as exc:
        raise_knowledge_error(
            exc
        )