from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query, Response

from app.db.tenant_dependency import TenantScope
from app.modules.api_keys.schemas import (
    APIKeyCreate,
    APIKeyPublic,
)
from app.modules.api_keys.service import APIKeyService


router = APIRouter(
    prefix="/workspaces/{workspace_id}/api-keys",
    tags=["API Keys"],
)


@router.get("", response_model=list[APIKeyPublic])
async def list_api_keys(
    workspace_id: UUID,
    scope: TenantScope,
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[APIKeyPublic]:
    return await APIKeyService(scope).list_keys(
        limit=limit,
        offset=offset,
    )


@router.post("", status_code=201)
async def create_api_key(
    workspace_id: UUID,
    payload: APIKeyCreate,
    scope: TenantScope,
    response: Response,
) -> dict:
    issued = await APIKeyService(scope).create_key(payload)

    response.headers["Cache-Control"] = "no-store"

    return {
        "key": issued.key.model_dump(mode="json"),
        "secret": issued.secret.get_secret_value(),
    }


@router.get("/{key_id}", response_model=APIKeyPublic)
async def get_api_key(
    workspace_id: UUID,
    key_id: UUID,
    scope: TenantScope,
) -> APIKeyPublic:
    return await APIKeyService(scope).get_key(key_id)


@router.post("/{key_id}/revoke", response_model=APIKeyPublic)
async def revoke_api_key(
    workspace_id: UUID,
    key_id: UUID,
    scope: TenantScope,
) -> APIKeyPublic:
    return await APIKeyService(scope).revoke_key(key_id)


@router.post("/{key_id}/rotate", status_code=201)
async def rotate_api_key(
    workspace_id: UUID,
    key_id: UUID,
    scope: TenantScope,
    response: Response,
) -> dict:
    issued = await APIKeyService(scope).rotate_key(key_id)

    response.headers["Cache-Control"] = "no-store"

    return {
        "key": issued.key.model_dump(mode="json"),
        "secret": issued.secret.get_secret_value(),
    }