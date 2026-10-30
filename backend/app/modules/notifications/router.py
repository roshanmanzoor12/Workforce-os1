from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.modules.notifications.schemas import (
    NotificationListResponse,
    NotificationMarkAllReadResponse,
    NotificationMutationResponse,
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
    NotificationUnreadCountResponse,
)
from app.modules.notifications.service import (
    NotificationNotFoundError,
    NotificationService,
)
from app.modules.tenant_api.dependencies import (
    get_authorized_tenant_context,
)


router = APIRouter(
    prefix="/notifications",
    tags=["notifications"],
)


TenantContext = Annotated[
    Any,
    Depends(get_authorized_tenant_context),
]


def _actor_user_id(context: Any) -> uuid.UUID:
    value = getattr(
        context,
        "actor_user_id",
        None,
    )

    try:
        if isinstance(value, uuid.UUID):
            return value

        return uuid.UUID(str(value))

    except (
        TypeError,
        ValueError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Authenticated workspace "
                "user is unavailable."
            ),
        ) from exc


def _workspace_id(context: Any) -> uuid.UUID:
    value = getattr(
        context,
        "workspace_id",
        None,
    )

    try:
        if isinstance(value, uuid.UUID):
            return value

        return uuid.UUID(str(value))

    except (
        TypeError,
        ValueError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Workspace context is unavailable.",
        ) from exc


def _service(
    context: Any,
) -> NotificationService:
    return NotificationService(
        context.tenant_session,
        workspace_id=_workspace_id(context),
    )


@router.get(
    "",
    response_model=NotificationListResponse,
)
async def list_notifications(
    context: TenantContext,
    unread_only: bool = Query(
        default=False,
    ),
    notification_type: str | None = Query(
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
) -> NotificationListResponse:
    return await _service(
        context,
    ).list_notifications(
        user_id=_actor_user_id(context),
        unread_only=unread_only,
        notification_type=notification_type,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/unread-count",
    response_model=NotificationUnreadCountResponse,
)
async def unread_count(
    context: TenantContext,
) -> NotificationUnreadCountResponse:
    return await _service(
        context,
    ).unread_count(
        user_id=_actor_user_id(context),
    )


@router.post(
    "/{notification_id}/read",
    response_model=NotificationMutationResponse,
)
async def mark_notification_read(
    notification_id: uuid.UUID,
    context: TenantContext,
) -> NotificationMutationResponse:
    try:
        return await _service(
            context,
        ).mark_read(
            notification_id=notification_id,
            user_id=_actor_user_id(context),
        )

    except NotificationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post(
    "/{notification_id}/unread",
    response_model=NotificationMutationResponse,
)
async def mark_notification_unread(
    notification_id: uuid.UUID,
    context: TenantContext,
) -> NotificationMutationResponse:
    try:
        return await _service(
            context,
        ).mark_unread(
            notification_id=notification_id,
            user_id=_actor_user_id(context),
        )

    except NotificationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post(
    "/read-all",
    response_model=NotificationMarkAllReadResponse,
)
async def mark_all_notifications_read(
    context: TenantContext,
) -> NotificationMarkAllReadResponse:
    return await _service(
        context,
    ).mark_all_read(
        user_id=_actor_user_id(context),
    )


@router.delete(
    "/{notification_id}",
    response_model=NotificationMutationResponse,
)
async def delete_notification(
    notification_id: uuid.UUID,
    context: TenantContext,
) -> NotificationMutationResponse:
    try:
        return await _service(
            context,
        ).delete_notification(
            notification_id=notification_id,
            user_id=_actor_user_id(context),
        )

    except NotificationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get(
    "/preferences",
    response_model=NotificationPreferenceResponse,
)
async def get_notification_preferences(
    context: TenantContext,
) -> NotificationPreferenceResponse:
    return await _service(
        context,
    ).preferences(
        user_id=_actor_user_id(context),
    )


@router.patch(
    "/preferences",
    response_model=NotificationPreferenceResponse,
)
async def update_notification_preferences(
    payload: NotificationPreferenceUpdate,
    context: TenantContext,
) -> NotificationPreferenceResponse:
    return await _service(
        context,
    ).update_preferences(
        user_id=_actor_user_id(context),
        payload=payload,
    )


__all__ = [
    "router",
]