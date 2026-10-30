from __future__ import annotations

import uuid

from fastapi import (
    APIRouter,
    Depends,
    status,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.core.database import get_control_db
from app.modules.auth.permissions import (
    get_current_verified_user,
)
from app.modules.memberships.enums import (
    WorkspaceMembershipRole,
)
from app.modules.memberships.schemas import (
    WorkspaceMembershipAccessResponse,
    WorkspaceMembershipCreateRequest,
    WorkspaceMembershipListResponse,
    WorkspaceMembershipResponse,
    WorkspaceMembershipRoleUpdateRequest,
)
from app.modules.memberships.service import (
    WorkspaceMembershipService,
)
from app.modules.workspaces.models import (
    WORKSPACE_ROLE_ADMIN,
    WORKSPACE_ROLE_OWNER,
)


router = APIRouter(
    prefix="/workspace-memberships",
    tags=["workspace-memberships"],
)


def user_id_from(
    user: object,
) -> uuid.UUID:
    value = getattr(
        user,
        "id",
    )

    if isinstance(
        value,
        uuid.UUID,
    ):
        return value

    return uuid.UUID(
        str(value)
    )


def service_from(
    session: AsyncSession,
) -> WorkspaceMembershipService:
    return WorkspaceMembershipService(
        session
    )


@router.post(
    "/{workspace_id}/bootstrap-owner",
    response_model=(
        WorkspaceMembershipResponse
    ),
    status_code=status.HTTP_200_OK,
)
async def bootstrap_workspace_owner(
    workspace_id: uuid.UUID,
    session: AsyncSession = Depends(
        get_control_db
    ),
    current_user=Depends(
        get_current_verified_user
    ),
) -> WorkspaceMembershipResponse:
    membership = (
        await service_from(
            session
        ).bootstrap_owner(
            workspace_id=workspace_id,
            user_id=user_id_from(
                current_user
            ),
        )
    )

    return (
        WorkspaceMembershipResponse
        .model_validate(
            membership
        )
    )


@router.get(
    "/{workspace_id}/me",
    response_model=(
        WorkspaceMembershipAccessResponse
    ),
)
async def get_my_workspace_membership(
    workspace_id: uuid.UUID,
    session: AsyncSession = Depends(
        get_control_db
    ),
    current_user=Depends(
        get_current_verified_user
    ),
) -> WorkspaceMembershipAccessResponse:
    user_id = user_id_from(
        current_user
    )

    membership = (
        await service_from(
            session
        ).get_my_membership(
            workspace_id=workspace_id,
            user_id=user_id,
        )
    )

    return (
        WorkspaceMembershipAccessResponse(
            workspace_id=workspace_id,
            user_id=user_id,
            is_member=True,
            role=(
                WorkspaceMembershipRole(
                    membership.role_key
                )
            ),
            status=membership.status,
            can_manage_members=(
                membership.role_key
                in {
                    WORKSPACE_ROLE_OWNER,
                    WORKSPACE_ROLE_ADMIN,
                }
            ),
        )
    )


@router.get(
    "/{workspace_id}",
    response_model=(
        WorkspaceMembershipListResponse
    ),
)
async def list_workspace_members(
    workspace_id: uuid.UUID,
    session: AsyncSession = Depends(
        get_control_db
    ),
    current_user=Depends(
        get_current_verified_user
    ),
) -> WorkspaceMembershipListResponse:
    items = (
        await service_from(
            session
        ).list_members(
            workspace_id=workspace_id,
            user_id=user_id_from(
                current_user
            ),
        )
    )

    return (
        WorkspaceMembershipListResponse(
            workspace_id=workspace_id,
            items=[
                WorkspaceMembershipResponse
                .model_validate(
                    item
                )
                for item in items
            ],
        )
    )


@router.post(
    "/{workspace_id}/members/{target_user_id}",
    response_model=(
        WorkspaceMembershipResponse
    ),
    status_code=status.HTTP_201_CREATED,
)
async def add_workspace_member(
    workspace_id: uuid.UUID,
    target_user_id: uuid.UUID,
    payload: (
        WorkspaceMembershipCreateRequest
    ),
    session: AsyncSession = Depends(
        get_control_db
    ),
    current_user=Depends(
        get_current_verified_user
    ),
) -> WorkspaceMembershipResponse:
    membership = (
        await service_from(
            session
        ).add_member(
            workspace_id=workspace_id,
            actor_user_id=user_id_from(
                current_user
            ),
            target_user_id=target_user_id,
            role=payload.role,
        )
    )

    return (
        WorkspaceMembershipResponse
        .model_validate(
            membership
        )
    )


@router.patch(
    (
        "/{workspace_id}/members/"
        "{target_user_id}/role"
    ),
    response_model=(
        WorkspaceMembershipResponse
    ),
)
async def update_workspace_member_role(
    workspace_id: uuid.UUID,
    target_user_id: uuid.UUID,
    payload: (
        WorkspaceMembershipRoleUpdateRequest
    ),
    session: AsyncSession = Depends(
        get_control_db
    ),
    current_user=Depends(
        get_current_verified_user
    ),
) -> WorkspaceMembershipResponse:
    membership = (
        await service_from(
            session
        ).update_role(
            workspace_id=workspace_id,
            actor_user_id=user_id_from(
                current_user
            ),
            target_user_id=target_user_id,
            role=payload.role,
        )
    )

    return (
        WorkspaceMembershipResponse
        .model_validate(
            membership
        )
    )


@router.delete(
    (
        "/{workspace_id}/members/"
        "{target_user_id}"
    ),
    response_model=(
        WorkspaceMembershipResponse
    ),
)
async def remove_workspace_member(
    workspace_id: uuid.UUID,
    target_user_id: uuid.UUID,
    session: AsyncSession = Depends(
        get_control_db
    ),
    current_user=Depends(
        get_current_verified_user
    ),
) -> WorkspaceMembershipResponse:
    membership = (
        await service_from(
            session
        ).remove_member(
            workspace_id=workspace_id,
            actor_user_id=user_id_from(
                current_user
            ),
            target_user_id=target_user_id,
        )
    )

    return (
        WorkspaceMembershipResponse
        .model_validate(
            membership
        )
    )