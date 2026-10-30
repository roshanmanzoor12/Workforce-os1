from __future__ import annotations

import uuid
from typing import (
    Annotated,
    Any,
)

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)

from app.core.exceptions import (
    ValidationError,
)
from app.modules.tenant_api.dependencies import (
    get_authorized_tenant_context,
)
from app.modules.workspace_search.access import (
    resolve_search_access,
)
from app.modules.workspace_search.enums import (
    SearchEntityType,
)
from app.modules.workspace_search.schemas import (
    SearchCapabilitiesResponse,
    WorkspaceSearchResponse,
)
from app.modules.workspace_search.service import (
    WorkspaceSearchService,
)


router = APIRouter(
    prefix=(
        "/workspaces/"
        "{workspace_id}/search"
    ),
    tags=[
        "workspace-search",
    ],
)


TenantContext = Annotated[
    Any,
    Depends(
        get_authorized_tenant_context
    ),
]


async def _access(
    *,
    workspace_id: uuid.UUID,
    context: Any,
):
    try:
        return await (
            resolve_search_access(
                workspace_id=workspace_id,
                context=context,
            )
        )

    except ValidationError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=str(
                exc
            ),
        ) from exc


@router.get(
    "",
    response_model=(
        WorkspaceSearchResponse
    ),
)
async def workspace_search(
    workspace_id: uuid.UUID,
    context: TenantContext,

    q: str = Query(
        min_length=2,
        max_length=200,
    ),

    types: (
        list[SearchEntityType]
        | None
    ) = Query(
        default=None,
    ),

    limit: int = Query(
        default=30,
        ge=1,
        le=100,
    ),
) -> WorkspaceSearchResponse:
    access = await _access(
        workspace_id=workspace_id,
        context=context,
    )

    service = (
        WorkspaceSearchService(
            context.tenant_session
        )
    )

    try:
        return await service.search(
            query=q,
            access=access,
            requested_types=types,
            limit=limit,
        )

    except ValidationError as exc:
        raise HTTPException(
            status_code=(
                status
                .HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail=str(
                exc
            ),
        ) from exc


@router.get(
    "/capabilities",
    response_model=(
        SearchCapabilitiesResponse
    ),
)
async def search_capabilities(
    workspace_id: uuid.UUID,
    context: TenantContext,
) -> SearchCapabilitiesResponse:
    access = await _access(
        workspace_id=workspace_id,
        context=context,
    )

    return (
        WorkspaceSearchService
        .capabilities(
            access=access
        )
    )


__all__ = [
    "router",
]