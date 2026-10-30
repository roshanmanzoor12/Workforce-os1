from __future__ import annotations

import uuid
from datetime import datetime
from typing import (
    Annotated,
    Any,
)

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)

from app.core.exceptions import (
    ValidationError,
)
from app.modules.audit_log.access import (
    resolve_audit_access,
)
from app.modules.audit_log.schemas import (
    AuditCapabilitiesResponse,
    AuditEventListResponse,
    AuditEventResponse,
)
from app.modules.audit_log.service import (
    AuditEventNotFoundError,
    AuditLogService,
)
from app.modules.tenant_api.dependencies import (
    get_authorized_tenant_context,
)


router = APIRouter(
    prefix=(
        "/workspaces/"
        "{workspace_id}/audit-log"
    ),
    tags=[
        "audit-log",
    ],
)


TenantContext = Annotated[
    Any,
    Depends(
        get_authorized_tenant_context
    ),
]


async def _require_access(
    *,
    workspace_id: uuid.UUID,
    context: Any,
):
    try:
        return await (
            resolve_audit_access(
                workspace_id=workspace_id,
                context=context,
            )
        )

    except ValidationError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=str(
                exc
            ),
        ) from exc


def _service(
    context: Any,
) -> AuditLogService:
    return AuditLogService(
        context.control_session
    )


@router.get(
    "",
    response_model=(
        AuditEventListResponse
    ),
)
async def list_audit_events(
    workspace_id: uuid.UUID,
    context: TenantContext,

    category: (
        str | None
    ) = Query(
        default=None,
    ),

    action: (
        str | None
    ) = Query(
        default=None,
    ),

    actor_user_id: (
        uuid.UUID | None
    ) = Query(
        default=None,
    ),

    target_type: (
        str | None
    ) = Query(
        default=None,
    ),

    target_id: (
        uuid.UUID | None
    ) = Query(
        default=None,
    ),

    outcome: (
        str | None
    ) = Query(
        default=None,
    ),

    severity: (
        str | None
    ) = Query(
        default=None,
    ),

    start_at: (
        datetime | None
    ) = Query(
        default=None,
    ),

    end_at: (
        datetime | None
    ) = Query(
        default=None,
    ),

    limit: int = Query(
        default=50,
        ge=1,
        le=200,
    ),

    offset: int = Query(
        default=0,
        ge=0,
    ),
) -> AuditEventListResponse:
    await _require_access(
        workspace_id=workspace_id,
        context=context,
    )

    try:
        return await (
            _service(
                context
            )
            .list_events(
                workspace_id=workspace_id,

                category=category,

                action=action,

                actor_user_id=(
                    actor_user_id
                ),

                target_type=(
                    target_type
                ),

                target_id=target_id,

                outcome=outcome,

                severity=severity,

                start_at=start_at,

                end_at=end_at,

                limit=limit,

                offset=offset,
            )
        )

    except ValidationError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail=str(
                exc
            ),
        ) from exc


@router.get(
    "/capabilities",
    response_model=(
        AuditCapabilitiesResponse
    ),
)
async def audit_capabilities(
    workspace_id: uuid.UUID,
    context: TenantContext,
) -> AuditCapabilitiesResponse:
    await _require_access(
        workspace_id=workspace_id,
        context=context,
    )

    return AuditCapabilitiesResponse()


@router.get(
    "/{event_id}",
    response_model=(
        AuditEventResponse
    ),
)
async def get_audit_event(
    workspace_id: uuid.UUID,
    event_id: uuid.UUID,
    context: TenantContext,
) -> AuditEventResponse:
    await _require_access(
        workspace_id=workspace_id,
        context=context,
    )

    try:
        return await (
            _service(
                context
            )
            .get(
                workspace_id=workspace_id,
                event_id=event_id,
            )
        )

    except AuditEventNotFoundError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=str(
                exc
            ),
        ) from exc


__all__ = [
    "router",
]