from __future__ import annotations

from fastapi import (
    APIRouter,
    HTTPException,
    status,
)

from app.db.tenant_dependency import (
    TenantScope,
)
from app.modules.ai_productivity.context_service import (
    AIActorEmployeeNotFoundError,
)
from app.modules.ai_productivity.provider import (
    AIProviderUnavailableError,
)
from app.modules.ai_productivity.schemas import (
    AIProductivityCapabilitiesResponse,
    AIProductivityRequest,
    AIProductivityResponse,
)
from app.modules.ai_productivity.service import (
    AIProductivityService,
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
        "{workspace_id}/ai-productivity"
    ),
    tags=[
        "ai-productivity",
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
) -> AIProductivityService:
    return AIProductivityService(
        scope.session
    )


@router.get(
    "/capabilities",
    response_model=(
        AIProductivityCapabilitiesResponse
    ),
)
async def capabilities(
    scope: TenantScope,
) -> AIProductivityCapabilitiesResponse:
    permissions(
        scope
    ).require(
        WorkspacePermission
        .AI_PRODUCTIVITY_USE
        .value
    )

    return service(
        scope
    ).capabilities()


@router.post(
    "/run",
    response_model=(
        AIProductivityResponse
    ),
)
async def run_ai_productivity(
    request: AIProductivityRequest,
    scope: TenantScope,
) -> AIProductivityResponse:
    permissions(
        scope
    ).require(
        WorkspacePermission
        .AI_PRODUCTIVITY_USE
        .value
    )

    try:
        return await service(
            scope
        ).execute(
            actor_user_id=(
                actor_user_id_from_scope(
                    scope
                )
            ),
            request=request,
        )

    except (
        AIActorEmployeeNotFoundError
    ) as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=str(exc),
        ) from exc

    except (
        AIProviderUnavailableError
    ) as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=str(exc),
        ) from exc