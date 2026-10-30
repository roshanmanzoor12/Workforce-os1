from __future__ import annotations

import uuid

from fastapi import APIRouter, status

from app.db.tenant_dependency import (
    ControlDB,
    VerifiedUser,
)
from app.modules.organizations.schemas import (
    OrganizationResponse,
    OrganizationUpdateRequest,
    OrganizationWorkspaceResponse,
)
from app.modules.organizations.service import (
    OrganizationService,
)


router = APIRouter(
    prefix="/organizations",
    tags=["Organizations"],
)


def organization_service(
    session: ControlDB,
    user: VerifiedUser,
) -> OrganizationService:
    return OrganizationService(
        session=session,
        user_id=user.id,
    )


@router.get(
    "/{organization_id}",
    response_model=OrganizationResponse,
    status_code=status.HTTP_200_OK,
)
async def get_organization(
    organization_id: uuid.UUID,
    session: ControlDB,
    user: VerifiedUser,
) -> OrganizationResponse:
    service = organization_service(
        session,
        user,
    )

    workspace = await service.get_organization(
        organization_id
    )

    return OrganizationResponse.model_validate(
        workspace
    )


@router.patch(
    "/{organization_id}",
    response_model=OrganizationResponse,
    status_code=status.HTTP_200_OK,
)
async def update_organization(
    organization_id: uuid.UUID,
    request: OrganizationUpdateRequest,
    session: ControlDB,
    user: VerifiedUser,
) -> OrganizationResponse:
    service = organization_service(
        session,
        user,
    )

    workspace = await service.update_organization(
        organization_id,
        request,
    )

    return OrganizationResponse.model_validate(
        workspace
    )


@router.get(
    "/{organization_id}/workspaces",
    response_model=list[OrganizationWorkspaceResponse],
    status_code=status.HTTP_200_OK,
)
async def list_organization_workspaces(
    organization_id: uuid.UUID,
    session: ControlDB,
    user: VerifiedUser,
) -> list[OrganizationWorkspaceResponse]:
    service = organization_service(
        session,
        user,
    )

    workspaces = await service.list_workspaces(
        organization_id
    )

    return [
        OrganizationWorkspaceResponse.model_validate(
            workspace
        )
        for workspace in workspaces
    ]


__all__ = [
    "router",
]