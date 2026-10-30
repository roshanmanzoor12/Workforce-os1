from __future__ import annotations

import uuid

from fastapi import (
    APIRouter,
    HTTPException,
    status,
)

from app.db.tenant_dependency import (
    TenantScope,
)
from app.modules.discipline.schemas import (
    IncidentCreate,
    IncidentList,
    IncidentPublic,
    IncidentUpdate,
)
from app.modules.discipline.service import (
    DisciplineService,
)


router = APIRouter(
    prefix=(
        "/workspaces/"
        "{workspace_id}/discipline"
    ),
    tags=["discipline"],
)


def discipline_service(
    scope: TenantScope,
) -> DisciplineService:
    return DisciplineService(
        scope.session,
        scope.user_id,
    )


@router.post(
    "/incidents",
    response_model=IncidentPublic,
    status_code=status.HTTP_201_CREATED,
)
async def create_incident(
    request: IncidentCreate,
    scope: TenantScope,
) -> IncidentPublic:
    return await discipline_service(
        scope
    ).create(request)


@router.get(
    "/incidents",
    response_model=IncidentList,
)
async def list_incidents(
    scope: TenantScope,
    employee_id: uuid.UUID | None = None,
) -> IncidentList:
    return await discipline_service(
        scope
    ).list(employee_id)


@router.patch(
    "/incidents/{incident_id}",
    response_model=IncidentPublic,
)
async def update_incident(
    incident_id: uuid.UUID,
    request: IncidentUpdate,
    scope: TenantScope,
) -> IncidentPublic:
    try:
        return await discipline_service(
            scope
        ).update(
            incident_id,
            request,
        )
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


__all__ = [
    "router",
]