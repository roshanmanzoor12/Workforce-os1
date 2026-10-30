from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, status

from app.modules.privacy.permissions import (
    require_privacy_access,
)
from app.modules.privacy.schemas import (
    PrivacyExclusionCreate,
    PrivacyExclusionPublic,
    PrivacyPolicyCreate,
    PrivacyPolicyPublic,
    PrivacyZoneCreate,
    PrivacyZonePublic,
)
from app.modules.privacy.service import PrivacyService


router = APIRouter(
    prefix="/workspaces/{workspace_id}/privacy",
    tags=["privacy"],
)

_service = PrivacyService()


@router.get(
    "/policies",
    response_model=list[PrivacyPolicyPublic],
)
async def list_privacy_policies(
    workspace_id: UUID,
) -> list[PrivacyPolicyPublic]:
    require_privacy_access()

    items = await _service.list_policies(workspace_id)

    return [
        PrivacyPolicyPublic.model_validate(item)
        for item in items
    ]


@router.post(
    "/policies",
    response_model=PrivacyPolicyPublic,
    status_code=status.HTTP_201_CREATED,
)
async def create_privacy_policy(
    workspace_id: UUID,
    request: PrivacyPolicyCreate,
) -> PrivacyPolicyPublic:
    require_privacy_access()

    item = await _service.create_policy(
        workspace_id=workspace_id,
        name=request.name,
        description=request.description,
    )

    return PrivacyPolicyPublic.model_validate(item)


@router.get(
    "/zones",
    response_model=list[PrivacyZonePublic],
)
async def list_privacy_zones(
    workspace_id: UUID,
) -> list[PrivacyZonePublic]:
    require_privacy_access()

    items = await _service.list_zones(workspace_id)

    return [
        PrivacyZonePublic.model_validate(item)
        for item in items
    ]


@router.post(
    "/zones",
    response_model=PrivacyZonePublic,
    status_code=status.HTTP_201_CREATED,
)
async def create_privacy_zone(
    workspace_id: UUID,
    request: PrivacyZoneCreate,
) -> PrivacyZonePublic:
    require_privacy_access()

    item = await _service.create_zone(
        workspace_id=workspace_id,
        name=request.name,
        zone_type=request.zone_type,
        value=request.value,
    )

    return PrivacyZonePublic.model_validate(item)


@router.get(
    "/exclusions",
    response_model=list[PrivacyExclusionPublic],
)
async def list_privacy_exclusions(
    workspace_id: UUID,
) -> list[PrivacyExclusionPublic]:
    require_privacy_access()

    items = await _service.list_exclusions(workspace_id)

    return [
        PrivacyExclusionPublic.model_validate(item)
        for item in items
    ]


@router.post(
    "/exclusions",
    response_model=PrivacyExclusionPublic,
    status_code=status.HTTP_201_CREATED,
)
async def create_privacy_exclusion(
    workspace_id: UUID,
    request: PrivacyExclusionCreate,
) -> PrivacyExclusionPublic:
    require_privacy_access()

    item = await _service.create_exclusion(
        workspace_id=workspace_id,
        exclusion_type=request.exclusion_type,
        value=request.value,
        reason=request.reason,
    )

    return PrivacyExclusionPublic.model_validate(item)