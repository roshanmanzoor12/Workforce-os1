from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    status,
)

from app.db.tenant_dependency import (
    TenantScope,
)
from app.modules.meetings.router import (
    actor_user_id_from_scope,
)
from app.modules.timeline.enums import (
    TimelineEventType,
    TimelineSourceKey,
)
from app.modules.timeline.factory import (
    build_timeline_query,
)
from app.modules.timeline.schemas import (
    TimelineCapabilities,
    TimelineResponse,
)
from app.modules.timeline.service import (
    TimelineEmployeeNotFoundError,
    TimelineService,
    TimelineValidationError,
)
from app.modules.workspace_permissions.permissions import (
    WorkspacePermission,
)
from app.modules.workspace_permissions.service import (
    WorkspacePermissionService,
)


router = APIRouter(
    prefix=(
        "/workspaces/"
        "{workspace_id}/timeline"
    ),
    tags=[
        "timeline",
    ],
)


def permission_service(
    scope: TenantScope,
) -> WorkspacePermissionService:
    return (
        WorkspacePermissionService(
            scope
        )
    )


def timeline_service(
    scope: TenantScope,
) -> TimelineService:
    return TimelineService(
        scope.session
    )


def raise_timeline_error(
    exc: Exception,
) -> None:
    if isinstance(
        exc,
        TimelineEmployeeNotFoundError,
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=str(
                exc
            ),
        ) from exc

    if isinstance(
        exc,
        TimelineValidationError,
    ):
        raise HTTPException(
            status_code=(
                status
                .HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail=str(
                exc
            ),
        ) from exc

    if isinstance(
        exc,
        ValueError,
    ):
        raise HTTPException(
            status_code=(
                status
                .HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail=str(
                exc
            ),
        ) from exc

    raise exc


@router.get(
    "/capabilities",
    response_model=(
        TimelineCapabilities
    ),
)
async def capabilities(
    scope: TenantScope,
) -> TimelineCapabilities:
    permissions = (
        permission_service(
            scope
        )
    )

    allowed = (
        permissions.has(
            WorkspacePermission
            .TIMELINE_SELF
            .value
        )
        or permissions.has(
            WorkspacePermission
            .TIMELINE_VIEW
            .value
        )
    )

    if not allowed:
        permissions.require(
            WorkspacePermission
            .TIMELINE_SELF
            .value
        )

    return (
        timeline_service(
            scope
        ).capabilities()
    )


@router.get(
    "/me",
    response_model=(
        TimelineResponse
    ),
)
async def my_timeline(
    scope: TenantScope,
    before: datetime | None = Query(
        default=None,
    ),
    after: datetime | None = Query(
        default=None,
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
    ),
    source: list[
        TimelineSourceKey
    ]
    | None = Query(
        default=None,
    ),
    event_type: list[
        TimelineEventType
    ]
    | None = Query(
        default=None,
    ),
    cursor: str | None = Query(
        default=None,
        max_length=2000,
    ),
) -> TimelineResponse:
    permission_service(
        scope
    ).require(
        WorkspacePermission
        .TIMELINE_SELF
        .value
    )

    try:
        query = (
            build_timeline_query(
                before=before,
                after=after,
                limit=limit,
                sources=source,
                event_types=(
                    event_type
                ),
                cursor=cursor,
            )
        )

        service = timeline_service(
            scope
        )

        employee = await (
            service
            .resolve_actor_employee(
                actor_user_id_from_scope(
                    scope
                )
            )
        )

        return await (
            service.list_timeline_query(
                employee_id=(
                    employee.id
                ),
                query=query,
            )
        )

    except Exception as exc:
        raise_timeline_error(
            exc
        )

        raise


@router.get(
    "/employees/{employee_id}",
    response_model=(
        TimelineResponse
    ),
)
async def employee_timeline(
    employee_id: uuid.UUID,
    scope: TenantScope,
    before: datetime | None = Query(
        default=None,
    ),
    after: datetime | None = Query(
        default=None,
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
    ),
    source: list[
        TimelineSourceKey
    ]
    | None = Query(
        default=None,
    ),
    event_type: list[
        TimelineEventType
    ]
    | None = Query(
        default=None,
    ),
    cursor: str | None = Query(
        default=None,
        max_length=2000,
    ),
) -> TimelineResponse:
    permission_service(
        scope
    ).require(
        WorkspacePermission
        .TIMELINE_VIEW
        .value
    )

    try:
        query = (
            build_timeline_query(
                before=before,
                after=after,
                limit=limit,
                sources=source,
                event_types=(
                    event_type
                ),
                cursor=cursor,
            )
        )

        return await (
            timeline_service(
                scope
            ).list_timeline_query(
                employee_id=(
                    employee_id
                ),
                query=query,
            )
        )

    except Exception as exc:
        raise_timeline_error(
            exc
        )

        raise