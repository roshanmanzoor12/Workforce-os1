from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    status,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.core.database import (
    get_control_db,
)
from app.modules.auth.models import User
from app.modules.auth.permissions import (
    get_current_verified_user,
)
from app.modules.workspace_invitations.schemas import (
    WorkspaceInvitationActionResponse,
    WorkspaceInvitationCreateRequest,
    WorkspaceInvitationListResponse,
    WorkspaceInvitationSecretResponse,
    WorkspaceInvitationTokenPublic,
)
from app.modules.workspace_invitations.service import (
    WorkspaceInvitationService,
)


# =========================================================
# DEPENDENCIES
# =========================================================

ControlDB = Annotated[
    AsyncSession,
    Depends(
        get_control_db
    ),
]


VerifiedUser = Annotated[
    User,
    Depends(
        get_current_verified_user
    ),
]


def get_workspace_invitation_service(
    session: ControlDB,
) -> WorkspaceInvitationService:
    return WorkspaceInvitationService(
        session
    )


InvitationService = Annotated[
    WorkspaceInvitationService,
    Depends(
        get_workspace_invitation_service
    ),
]


# =========================================================
# WORKSPACE-SCOPED ROUTER
# =========================================================

workspace_router = APIRouter(
    prefix=(
        "/workspaces/"
        "{workspace_id}/invitations"
    ),
    tags=[
        "workspace-invitations",
    ],
)


@workspace_router.post(
    "",
    response_model=(
        WorkspaceInvitationSecretResponse
    ),
    status_code=(
        status.HTTP_201_CREATED
    ),
)
async def create_workspace_invitation(
    workspace_id: uuid.UUID,
    payload: WorkspaceInvitationCreateRequest,
    service: InvitationService,
    current_user: VerifiedUser,
) -> WorkspaceInvitationSecretResponse:
    return await service.create_invitation(
        payload,
        workspace_id=workspace_id,
        user=current_user,
    )


@workspace_router.get(
    "",
    response_model=(
        WorkspaceInvitationListResponse
    ),
)
async def list_workspace_invitations(
    workspace_id: uuid.UUID,
    service: InvitationService,
    current_user: VerifiedUser,
) -> WorkspaceInvitationListResponse:
    return await service.list_invitations(
        workspace_id=workspace_id,
        user=current_user,
    )


@workspace_router.post(
    "/{invitation_id}/resend",
    response_model=(
        WorkspaceInvitationSecretResponse
    ),
)
async def resend_workspace_invitation(
    workspace_id: uuid.UUID,
    invitation_id: uuid.UUID,
    service: InvitationService,
    current_user: VerifiedUser,
) -> WorkspaceInvitationSecretResponse:
    return await service.resend(
        workspace_id=workspace_id,
        invitation_id=invitation_id,
        user=current_user,
    )


@workspace_router.delete(
    "/{invitation_id}",
    response_model=(
        WorkspaceInvitationActionResponse
    ),
)
async def revoke_workspace_invitation(
    workspace_id: uuid.UUID,
    invitation_id: uuid.UUID,
    service: InvitationService,
    current_user: VerifiedUser,
) -> WorkspaceInvitationActionResponse:
    return await service.revoke(
        workspace_id=workspace_id,
        invitation_id=invitation_id,
        user=current_user,
    )


# =========================================================
# TOKEN ROUTER
# =========================================================

token_router = APIRouter(
    prefix="/workspace-invitations",
    tags=[
        "workspace-invitations",
    ],
)


@token_router.get("/incoming")
async def incoming_workspace_invitations(
    service: InvitationService,
    current_user: VerifiedUser,
):
    return await service.list_incoming(user=current_user)


@token_router.post("/incoming/{invitation_id}/accept", response_model=WorkspaceInvitationActionResponse)
async def accept_incoming_invitation(
    invitation_id: uuid.UUID,
    service: InvitationService,
    current_user: VerifiedUser,
) -> WorkspaceInvitationActionResponse:
    return await service.accept_by_id(invitation_id=invitation_id, user=current_user)


@token_router.post("/incoming/{invitation_id}/decline", response_model=WorkspaceInvitationActionResponse)
async def decline_incoming_invitation(
    invitation_id: uuid.UUID,
    service: InvitationService,
    current_user: VerifiedUser,
) -> WorkspaceInvitationActionResponse:
    return await service.decline_by_id(invitation_id=invitation_id, user=current_user)


@token_router.get(
    "/{token}",
    response_model=(
        WorkspaceInvitationTokenPublic
    ),
)
async def get_workspace_invitation(
    token: str,
    service: InvitationService,
    current_user: VerifiedUser,
) -> WorkspaceInvitationTokenPublic:
    return await (
        service.get_token_invitation(
            token=token,
            user=current_user,
        )
    )


@token_router.post(
    "/{token}/accept",
    response_model=(
        WorkspaceInvitationActionResponse
    ),
)
async def accept_workspace_invitation(
    token: str,
    service: InvitationService,
    current_user: VerifiedUser,
) -> WorkspaceInvitationActionResponse:
    return await service.accept(
        token=token,
        user=current_user,
    )


@token_router.post(
    "/{token}/decline",
    response_model=(
        WorkspaceInvitationActionResponse
    ),
)
async def decline_workspace_invitation(
    token: str,
    service: InvitationService,
    current_user: VerifiedUser,
) -> WorkspaceInvitationActionResponse:
    return await service.decline(
        token=token,
        user=current_user,
    )


# =========================================================
# ROOT ROUTER
# =========================================================

router = APIRouter()

router.include_router(
    workspace_router
)

router.include_router(
    token_router
)


__all__ = [
    "router",
    "workspace_router",
    "token_router",
]
