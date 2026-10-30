from __future__ import annotations

import uuid

from fastapi import APIRouter, status

from app.modules.workspace_rbac.scope_api_contract import (
    SCOPE_API_PREFIX,
    SCOPE_DELETE_SUFFIX,
)
from app.modules.workspace_rbac.scope_dependencies import (
    MembershipScopeServiceDep,
)
from app.modules.workspace_rbac.scope_schemas import (
    SavedScopeType,
    ScopeGrantCreateRequest,
    ScopeGrantDeleteResponse,
    ScopeGrantListResponse,
    ScopeGrantPublic,
)


router = APIRouter(
    prefix=SCOPE_API_PREFIX,
    tags=["Workspace Member Scopes"],
)


@router.get(
    "",
    response_model=ScopeGrantListResponse,
    summary="List saved member scopes",
)
async def list_member_scopes(
    membership_id: uuid.UUID,
    service: MembershipScopeServiceDep,
) -> ScopeGrantListResponse:
    return await service.list_for(
        membership_id=membership_id,
    )


@router.post(
    "",
    response_model=ScopeGrantPublic,
    status_code=status.HTTP_200_OK,
    summary="Grant a saved member scope",
    description=(
        "Grant an active department or team resource to a workspace "
        "membership. Repeating the same grant returns the existing "
        "record. This operation does not grant permissions."
    ),
)
async def grant_member_scope(
    membership_id: uuid.UUID,
    payload: ScopeGrantCreateRequest,
    service: MembershipScopeServiceDep,
) -> ScopeGrantPublic:
    return await service.grant(
        payload,
        membership_id=membership_id,
    )


@router.delete(
    SCOPE_DELETE_SUFFIX,
    response_model=ScopeGrantDeleteResponse,
    summary="Revoke a saved member scope",
    description=(
        "Remove a department or team grant. An already absent grant "
        "returns removed=false. Cleanup remains possible when the "
        "target membership or resource is inactive."
    ),
)
async def revoke_member_scope(
    membership_id: uuid.UUID,
    scope_type: SavedScopeType,
    resource_id: uuid.UUID,
    service: MembershipScopeServiceDep,
) -> ScopeGrantDeleteResponse:
    return await service.revoke(
        membership_id=membership_id,
        scope_type=scope_type,
        resource_id=resource_id,
    )


__all__ = [
    "router",
    "list_member_scopes",
    "grant_member_scope",
    "revoke_member_scope",
]