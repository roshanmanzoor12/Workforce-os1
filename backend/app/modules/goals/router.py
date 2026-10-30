from __future__ import annotations

import uuid

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)

from app.db.tenant_dependency import (
    TenantScope,
)
from app.modules.goals.schemas import (
    GoalCreateRequest,
    GoalListResponse,
    GoalPublic,
    GoalUpdateRequest,
)
from app.modules.goals.self_service import (
    GoalActorEmployeeNotFoundError,
    GoalSelfService,
)
from app.modules.goals.service import (
    GoalNotFoundError,
    GoalService,
    GoalValidationError,
)
from app.modules.meetings.router import (
    actor_user_id_from_scope,
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
        "{workspace_id}/goals"
    ),
    tags=[
        "goals",
    ],
)


def goal_service(
    scope: TenantScope,
) -> GoalService:
    return GoalService(
        scope.session
    )


def goal_self_service(
    scope: TenantScope,
) -> GoalSelfService:
    return GoalSelfService(
        scope.session
    )


def permission_service(
    scope: TenantScope,
) -> WorkspacePermissionService:
    return WorkspacePermissionService(
        scope
    )


def raise_goal_error(
    exc: Exception,
) -> None:
    if isinstance(
        exc,
        GoalNotFoundError,
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=str(exc),
        ) from exc

    if isinstance(
        exc,
        GoalActorEmployeeNotFoundError,
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=str(exc),
        ) from exc

    if isinstance(
        exc,
        GoalValidationError,
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail=str(exc),
        ) from exc

    raise exc


@router.get(
    "/me",
    response_model=GoalListResponse,
)
async def list_my_goals(
    scope: TenantScope,
) -> GoalListResponse:
    permissions = permission_service(
        scope
    )

    permissions.require(
        WorkspacePermission
        .GOALS_SELF
        .value
    )

    service = goal_self_service(
        scope
    )

    try:
        return await (
            service.list_my_goals(
                actor_user_id_from_scope(
                    scope
                )
            )
        )
    except Exception as exc:
        raise_goal_error(
            exc
        )
        raise


@router.post(
    "/me",
    response_model=GoalPublic,
    status_code=(
        status.HTTP_201_CREATED
    ),
)
async def create_my_goal(
    request: GoalCreateRequest,
    scope: TenantScope,
) -> GoalPublic:
    permissions = permission_service(
        scope
    )

    permissions.require(
        WorkspacePermission
        .GOALS_SELF
        .value
    )

    service = goal_self_service(
        scope
    )

    try:
        return await (
            service.create_my_goal(
                actor_user_id_from_scope(
                    scope
                ),
                request,
            )
        )
    except Exception as exc:
        raise_goal_error(
            exc
        )
        raise


@router.get(
    "/me/{goal_id}",
    response_model=GoalPublic,
)
async def get_my_goal(
    goal_id: uuid.UUID,
    scope: TenantScope,
) -> GoalPublic:
    permission_service(
        scope
    ).require(
        WorkspacePermission
        .GOALS_SELF
        .value
    )

    try:
        return await (
            goal_self_service(
                scope
            ).get_my_goal(
                actor_user_id_from_scope(
                    scope
                ),
                goal_id,
            )
        )
    except Exception as exc:
        raise_goal_error(
            exc
        )
        raise


@router.patch(
    "/me/{goal_id}",
    response_model=GoalPublic,
)
async def update_my_goal(
    goal_id: uuid.UUID,
    request: GoalUpdateRequest,
    scope: TenantScope,
) -> GoalPublic:
    permission_service(
        scope
    ).require(
        WorkspacePermission
        .GOALS_SELF
        .value
    )

    try:
        return await (
            goal_self_service(
                scope
            ).update_my_goal(
                actor_user_id_from_scope(
                    scope
                ),
                goal_id,
                request,
            )
        )
    except Exception as exc:
        raise_goal_error(
            exc
        )
        raise


@router.delete(
    "/me/{goal_id}",
    status_code=(
        status.HTTP_204_NO_CONTENT
    ),
)
async def delete_my_goal(
    goal_id: uuid.UUID,
    scope: TenantScope,
) -> None:
    permission_service(
        scope
    ).require(
        WorkspacePermission
        .GOALS_SELF
        .value
    )

    try:
        await (
            goal_self_service(
                scope
            ).delete_my_goal(
                actor_user_id_from_scope(
                    scope
                ),
                goal_id,
            )
        )
    except Exception as exc:
        raise_goal_error(
            exc
        )


@router.get(
    "/employee/{employee_id}",
    response_model=GoalListResponse,
)
async def list_employee_goals(
    employee_id: uuid.UUID,
    scope: TenantScope,
) -> GoalListResponse:
    permission_service(
        scope
    ).require(
        WorkspacePermission
        .GOALS_VIEW
        .value
    )

    return await (
        goal_service(
            scope
        ).list_employee_goals(
            employee_id
        )
    )


@router.get(
    "/{goal_id}",
    response_model=GoalPublic,
)
async def get_goal(
    goal_id: uuid.UUID,
    scope: TenantScope,
) -> GoalPublic:
    permission_service(
        scope
    ).require(
        WorkspacePermission
        .GOALS_VIEW
        .value
    )

    try:
        return await (
            goal_service(
                scope
            ).get_goal(
                goal_id
            )
        )
    except Exception as exc:
        raise_goal_error(
            exc
        )
        raise


@router.patch(
    "/{goal_id}",
    response_model=GoalPublic,
)
async def update_goal(
    goal_id: uuid.UUID,
    request: GoalUpdateRequest,
    scope: TenantScope,
) -> GoalPublic:
    permission_service(
        scope
    ).require(
        WorkspacePermission
        .GOALS_MANAGE
        .value
    )

    try:
        return await (
            goal_service(
                scope
            ).update_goal(
                goal_id,
                request,
            )
        )
    except Exception as exc:
        raise_goal_error(
            exc
        )
        raise


@router.delete(
    "/{goal_id}",
    status_code=(
        status.HTTP_204_NO_CONTENT
    ),
)
async def delete_goal(
    goal_id: uuid.UUID,
    scope: TenantScope,
) -> None:
    permission_service(
        scope
    ).require(
        WorkspacePermission
        .GOALS_MANAGE
        .value
    )

    try:
        await (
            goal_service(
                scope
            ).delete_goal(
                goal_id
            )
        )
    except Exception as exc:
        raise_goal_error(
            exc
        )