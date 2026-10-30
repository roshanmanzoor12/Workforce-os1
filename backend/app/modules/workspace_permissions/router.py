from __future__ import annotations

import uuid

from fastapi import (
    APIRouter,
    Body,
    Query,
    status,
)

from app.core.exceptions import ValidationError
from app.db.tenant_dependency import TenantScope
from app.modules.workspace_permissions.permissions import (
    ALL_WORKSPACE_PERMISSIONS,
)
from app.modules.workspace_permissions.roles import (
    BUILT_IN_ROLE_KEYS,
    ROLE_DISPLAY_NAMES,
    ROLE_PERMISSIONS,
)
from app.modules.workspace_permissions.schemas import (
    WorkspacePermissionCatalogResponse,
    WorkspacePermissionCheckManyResponse,
    WorkspacePermissionCheckRequest,
    WorkspacePermissionCheckResponse,
    WorkspacePermissionListResponse,
    WorkspacePermissionWorkspaceListResponse,
    WorkspaceRoleListResponse,
    WorkspaceRoleResponse,
)
from app.modules.workspace_permissions.service import (
    WorkspacePermissionService,
)
from app.modules.workspace_permissions.tenant_scope import (
    get_scope_role,
)


router = APIRouter(
    prefix="/workspaces/{workspace_id}/permissions",
    tags=["Workspace Permissions"],
)


def service_from(
    scope: TenantScope,
) -> WorkspacePermissionService:
    return WorkspacePermissionService(scope)


def role_from(
    scope: TenantScope,
) -> str:
    role_key = get_scope_role(scope)

    if role_key is None:
        raise ValidationError(
            "Workspace role is unavailable."
        )

    return role_key


@router.get(
    "/me",
    response_model=WorkspacePermissionListResponse,
    status_code=status.HTTP_200_OK,
    summary="List current workspace permissions",
)
async def get_my_permissions(
    workspace_id: uuid.UUID,
    scope: TenantScope,
) -> WorkspacePermissionListResponse:
    service = service_from(scope)
    permissions = service.list()

    return WorkspacePermissionListResponse(
        role_key=role_from(scope),
        permissions=permissions,
        total=len(permissions),
    )


@router.get(
    "/check",
    response_model=WorkspacePermissionCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Check workspace permission",
)
async def check_permission(
    workspace_id: uuid.UUID,
    scope: TenantScope,
    permission: str = Query(
        ...,
        min_length=1,
        max_length=128,
    ),
) -> WorkspacePermissionCheckResponse:
    return WorkspacePermissionCheckResponse(
        permission=permission,
        allowed=service_from(scope).has(permission),
    )


@router.post(
    "/check-many",
    response_model=WorkspacePermissionCheckManyResponse,
    status_code=status.HTTP_200_OK,
    summary="Check multiple workspace permissions",
)
async def check_many_permissions(
    workspace_id: uuid.UUID,
    scope: TenantScope,
    payload: WorkspacePermissionCheckRequest = Body(...),
) -> WorkspacePermissionCheckManyResponse:
    service = service_from(scope)
    role_key = role_from(scope)
    results = service.check_many(payload.permissions)

    return WorkspacePermissionCheckManyResponse(
        workspace_id=workspace_id,
        role_key=role_key,
        results=results,
        allows_all=all(results.values()),
        allows_any=any(results.values()),
    )


@router.get(
    "/catalog",
    response_model=WorkspacePermissionCatalogResponse,
    status_code=status.HTTP_200_OK,
    summary="List workspace permission catalog",
)
async def permission_catalog(
    workspace_id: uuid.UUID,
    scope: TenantScope,
) -> WorkspacePermissionCatalogResponse:
    _ = scope

    permissions = sorted(
        ALL_WORKSPACE_PERMISSIONS
    )

    return WorkspacePermissionCatalogResponse(
        permissions=permissions,
        total=len(permissions),
    )


@router.get(
    "/roles",
    response_model=WorkspaceRoleListResponse,
    status_code=status.HTTP_200_OK,
    summary="List built-in workspace roles",
)
async def list_workspace_roles(
    workspace_id: uuid.UUID,
    scope: TenantScope,
) -> WorkspaceRoleListResponse:
    _ = scope

    items = [
        WorkspaceRoleResponse(
            key=role_key,
            label=ROLE_DISPLAY_NAMES.get(
                role_key,
                role_key.replace(
                    "_",
                    " ",
                ).title(),
            ),
            permissions=sorted(
                ROLE_PERMISSIONS.get(
                    role_key,
                    frozenset(),
                )
            ),
        )
        for role_key in sorted(
            BUILT_IN_ROLE_KEYS
        )
    ]

    return WorkspaceRoleListResponse(
        workspace_id=workspace_id,
        items=items,
    )


@router.get(
    "/context",
    response_model=WorkspacePermissionWorkspaceListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current workspace permission context",
)
async def get_permission_context(
    workspace_id: uuid.UUID,
    scope: TenantScope,
) -> WorkspacePermissionWorkspaceListResponse:
    service = service_from(scope)

    return WorkspacePermissionWorkspaceListResponse(
        workspace_id=workspace_id,
        role_key=role_from(scope),
        permissions=service.list(),
    )


__all__ = [
    "router",
]