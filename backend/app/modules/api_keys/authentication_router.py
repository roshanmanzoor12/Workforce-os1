from typing import Annotated

from fastapi import APIRouter, Depends, Response

from app.modules.api_keys.authentication import APIKeyPrincipal
from app.modules.api_keys.authentication_dependency import (
    require_api_key,
)


router = APIRouter(
    prefix="/workspaces/{workspace_id}/api-key-auth",
    tags=["API key authentication"],
)


@router.get("/context")
async def get_api_key_context(
    principal: Annotated[
        APIKeyPrincipal,
        Depends(require_api_key()),
    ],
    response: Response,
) -> dict:
    response.headers["Cache-Control"] = "no-store"

    return {
        "key_id": str(principal.key_id),
        "workspace_id": str(principal.workspace_id),
        "user_id": str(principal.user_id),
        "membership_id": str(principal.membership_id),
        "scopes": sorted(principal.scopes),
    }