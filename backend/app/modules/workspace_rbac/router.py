from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_control_db
from app.modules.auth.models import User
from app.modules.auth.permissions import get_current_verified_user
from app.modules.workspace_rbac.schemas import (
    PermissionCatalogResponse,
    WorkspaceBootstrapResponse,
    WorkspaceMemberListResponse,
    WorkspaceMemberPublic,
    WorkspaceMemberRoleUpdateRequest,
    WorkspaceMemberRolesResponse,
    WorkspaceMemberVisibilityRequest,
    WorkspaceModerationActionResponse,
    WorkspaceRoleCreateRequest,
    WorkspaceRoleListResponse,
    WorkspaceRolePublic,
    WorkspaceRoleUpdateRequest,
)
from app.modules.workspace_rbac.service import WorkspaceRBACService


router = APIRouter(
    prefix="/workspaces/{workspace_id}",
    tags=["workspace-rbac"],
)

ControlDB = Annotated[AsyncSession, Depends(get_control_db)]
VerifiedUser = Annotated[User, Depends(get_current_verified_user)]


def get_service(session: ControlDB) -> WorkspaceRBACService:
    return WorkspaceRBACService(session)


ServiceDependency = Annotated[
    WorkspaceRBACService,
    Depends(get_service),
]


@router.get("/permissions", response_model=PermissionCatalogResponse)
async def permissions(
    workspace_id: uuid.UUID,
    service: ServiceDependency,
    user: VerifiedUser,
) -> PermissionCatalogResponse:
    return await service.permission_catalog(
        workspace_id=workspace_id,
        user=user,
    )


@router.get("/roles", response_model=WorkspaceRoleListResponse)
async def roles(
    workspace_id: uuid.UUID,
    service: ServiceDependency,
    user: VerifiedUser,
) -> WorkspaceRoleListResponse:
    return await service.list_roles(
        workspace_id=workspace_id,
        user=user,
    )


@router.put("/roles/builtin/{role_key}", response_model=WorkspaceRolePublic)
async def update_builtin_workspace_role(
    workspace_id: uuid.UUID,
    role_key: str,
    payload: WorkspaceRoleUpdateRequest,
    service: ServiceDependency,
    user: VerifiedUser,
) -> WorkspaceRolePublic:
    if payload.permissions is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="permissions list is required")
    return await service.update_builtin_role(
        workspace_id=workspace_id, role_key=role_key,
        permissions=payload.permissions, user=user,
    )


@router.post(
    "/roles",
    response_model=WorkspaceRolePublic,
    status_code=status.HTTP_201_CREATED,
)
async def create_role(
    workspace_id: uuid.UUID,
    payload: WorkspaceRoleCreateRequest,
    service: ServiceDependency,
    user: VerifiedUser,
) -> WorkspaceRolePublic:
    return await service.create_role(
        payload,
        workspace_id=workspace_id,
        user=user,
    )


@router.patch("/roles/{role_id}", response_model=WorkspaceRolePublic)
async def update_role(
    workspace_id: uuid.UUID,
    role_id: uuid.UUID,
    payload: WorkspaceRoleUpdateRequest,
    service: ServiceDependency,
    user: VerifiedUser,
) -> WorkspaceRolePublic:
    return await service.update_role(
        payload,
        workspace_id=workspace_id,
        role_id=role_id,
        user=user,
    )


@router.delete(
    "/roles/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_role(
    workspace_id: uuid.UUID,
    role_id: uuid.UUID,
    service: ServiceDependency,
    user: VerifiedUser,
) -> Response:
    await service.delete_role(
        workspace_id=workspace_id,
        role_id=role_id,
        user=user,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/members", response_model=WorkspaceMemberListResponse)
async def members(
    workspace_id: uuid.UUID,
    service: ServiceDependency,
    user: VerifiedUser,
) -> WorkspaceMemberListResponse:
    return await service.list_members(
        workspace_id=workspace_id,
        user=user,
    )


@router.patch(
    "/members/{membership_id}/role",
    response_model=WorkspaceMemberPublic,
)
async def update_member_role(
    workspace_id: uuid.UUID,
    membership_id: uuid.UUID,
    payload: WorkspaceMemberRoleUpdateRequest,
    service: ServiceDependency,
    user: VerifiedUser,
) -> WorkspaceMemberPublic:
    return await service.update_member_role(
        payload,
        workspace_id=workspace_id,
        membership_id=membership_id,
        user=user,
    )


@router.get(
    "/members/{membership_id}/roles",
    response_model=WorkspaceMemberRolesResponse,
)
async def member_roles(
    workspace_id: uuid.UUID,
    membership_id: uuid.UUID,
    service: ServiceDependency,
    user: VerifiedUser,
) -> WorkspaceMemberRolesResponse:
    return await service.get_member_roles(
        workspace_id=workspace_id,
        membership_id=membership_id,
        user=user,
    )


@router.put(
    "/members/{membership_id}/roles/{role_key}",
    response_model=WorkspaceMemberRolesResponse,
)
async def grant_member_role(
    workspace_id: uuid.UUID,
    membership_id: uuid.UUID,
    role_key: str,
    service: ServiceDependency,
    user: VerifiedUser,
) -> WorkspaceMemberRolesResponse:
    return await service.grant_member_role(
        workspace_id=workspace_id,
        membership_id=membership_id,
        role_key=role_key,
        user=user,
    )


@router.delete(
    "/members/{membership_id}/roles/{role_key}",
    response_model=WorkspaceMemberRolesResponse,
)
async def revoke_member_role(
    workspace_id: uuid.UUID,
    membership_id: uuid.UUID,
    role_key: str,
    service: ServiceDependency,
    user: VerifiedUser,
) -> WorkspaceMemberRolesResponse:
    return await service.revoke_member_role(
        workspace_id=workspace_id,
        membership_id=membership_id,
        role_key=role_key,
        user=user,
    )


@router.post(
    "/members/{membership_id}/kick",
    response_model=WorkspaceModerationActionResponse,
)
async def kick_member(
    workspace_id: uuid.UUID,
    membership_id: uuid.UUID,
    service: ServiceDependency,
    user: VerifiedUser,
) -> WorkspaceModerationActionResponse:
    return await service.kick_member(
        workspace_id=workspace_id,
        membership_id=membership_id,
        user=user,
    )


@router.post(
    "/members/{membership_id}/ban",
    response_model=WorkspaceModerationActionResponse,
)
async def ban_member(
    workspace_id: uuid.UUID,
    membership_id: uuid.UUID,
    service: ServiceDependency,
    user: VerifiedUser,
) -> WorkspaceModerationActionResponse:
    return await service.ban_member(
        workspace_id=workspace_id,
        membership_id=membership_id,
        user=user,
    )


@router.post(
    "/members/{membership_id}/mute",
    response_model=WorkspaceModerationActionResponse,
)
async def mute_member(
    workspace_id: uuid.UUID,
    membership_id: uuid.UUID,
    service: ServiceDependency,
    user: VerifiedUser,
) -> WorkspaceModerationActionResponse:
    return await service.mute_member(
        workspace_id=workspace_id,
        membership_id=membership_id,
        user=user,
    )


@router.post(
    "/members/{membership_id}/deafen",
    response_model=WorkspaceModerationActionResponse,
)
async def deafen_member(
    workspace_id: uuid.UUID,
    membership_id: uuid.UUID,
    service: ServiceDependency,
    user: VerifiedUser,
) -> WorkspaceModerationActionResponse:
    return await service.deafen_member(
        workspace_id=workspace_id,
        membership_id=membership_id,
        user=user,
    )


@router.patch(
    "/members/{membership_id}/visibility",
    response_model=WorkspaceModerationActionResponse,
)
async def member_visibility(
    workspace_id: uuid.UUID,
    membership_id: uuid.UUID,
    payload: WorkspaceMemberVisibilityRequest,
    service: ServiceDependency,
    user: VerifiedUser,
) -> WorkspaceModerationActionResponse:
    return await service.update_visibility(
        payload,
        workspace_id=workspace_id,
        membership_id=membership_id,
        user=user,
    )


@router.get("/bootstrap", response_model=WorkspaceBootstrapResponse)
async def bootstrap(
    workspace_id: uuid.UUID,
    service: ServiceDependency,
    user: VerifiedUser,
) -> WorkspaceBootstrapResponse:
    return await service.bootstrap(
        workspace_id=workspace_id,
        user=user,
    )


__all__ = ["router"]