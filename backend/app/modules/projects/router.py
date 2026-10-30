from uuid import UUID

from fastapi import APIRouter, Query, Response

from app.db.tenant_dependency import TenantScope
from app.modules.projects.access import (
    resolve_project_access,
    validate_context_identity,
)
from app.modules.projects.permissions import require_project_permission
from app.modules.projects.schemas import (
    ProjectCreate,
    ProjectList,
    ProjectPublic,
    ProjectStatus,
    ProjectUpdate,
)
from app.modules.projects.scoped_service import ScopedProjectService
from app.modules.workspace_permissions.request_scopes import (
    resolve_request_saved_scopes,
)


router = APIRouter(
    prefix="/workspaces/{workspace_id}/projects",
    tags=["projects"],
)


async def get_project_service(
    scope: TenantScope,
    *,
    manage: bool = False,
) -> ScopedProjectService:
    # Reject missing permissions before resolving tenant mappings.
    require_project_permission(scope, manage=manage)

    context = await resolve_project_access(scope)
    validate_context_identity(scope, context)

    context = await resolve_request_saved_scopes(
        scope,
        context,
    )
    validate_context_identity(scope, context)

    return ScopedProjectService(scope.session, context)


@router.post("", response_model=ProjectPublic, status_code=201)
async def create_project(request: ProjectCreate, scope: TenantScope):
    service = await get_project_service(scope, manage=True)

    try:
        result = await service.create(request)
        response = ProjectPublic.model_validate(result)
        await scope.session.commit()
        return response
    except Exception:
        await scope.session.rollback()
        raise


@router.get("", response_model=ProjectList)
async def list_projects(
    scope: TenantScope,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    status: ProjectStatus | None = None,
):
    service = await get_project_service(scope)

    items, total = await service.list(
        offset=offset,
        limit=limit,
        status=status,
    )

    return ProjectList(
        items=[ProjectPublic.model_validate(item) for item in items],
        total=total,
    )


@router.get("/{project_id}", response_model=ProjectPublic)
async def get_project(project_id: UUID, scope: TenantScope):
    service = await get_project_service(scope)
    result = await service.get(project_id)
    return ProjectPublic.model_validate(result)


@router.patch("/{project_id}", response_model=ProjectPublic)
async def update_project(
    project_id: UUID,
    request: ProjectUpdate,
    scope: TenantScope,
):
    service = await get_project_service(scope, manage=True)

    try:
        result = await service.update(project_id, request)
        response = ProjectPublic.model_validate(result)
        await scope.session.commit()
        return response
    except Exception:
        await scope.session.rollback()
        raise


@router.delete(
    "/{project_id}",
    status_code=204,
    response_class=Response,
)
async def delete_project(project_id: UUID, scope: TenantScope):
    service = await get_project_service(scope, manage=True)

    try:
        await service.delete(project_id)
        await scope.session.commit()
        return Response(status_code=204)
    except Exception:
        await scope.session.rollback()
        raise


__all__ = ["get_project_service", "router"]