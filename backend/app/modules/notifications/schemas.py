from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class NotificationSchema(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True,
    )


# =========================================================
# NOTIFICATION RESPONSE
# =========================================================


class NotificationResponse(
    NotificationSchema
):
    id: uuid.UUID

    recipient_user_id: uuid.UUID

    notification_type: str

    title: str

    body: str | None

    priority: str

    entity_type: str | None
    entity_id: uuid.UUID | None

    action_url: str | None

    payload: dict

    read_at: datetime | None

    created_at: datetime
    updated_at: datetime


class NotificationListResponse(
    NotificationSchema
):
    items: list[
        NotificationResponse
    ] = Field(
        default_factory=list
    )

    total: int

    unread_count: int

    limit: int
    offset: int


class NotificationUnreadCountResponse(
    NotificationSchema
):
    unread_count: int


class NotificationMutationResponse(
    NotificationSchema
):
    id: uuid.UUID

    read_at: datetime | None


class NotificationMarkAllReadResponse(
    NotificationSchema
):
    updated_count: int


# =========================================================
# PREFERENCES
# =========================================================


class NotificationPreferenceResponse(
    NotificationSchema
):
    in_app_enabled: bool

    email_enabled: bool

    push_enabled: bool

    sound_enabled: bool

    digest_enabled: bool

    digest_hour: int

    muted_types: list[str] = Field(
        default_factory=list
    )


class NotificationPreferenceUpdate(
    NotificationSchema
):
    in_app_enabled: (
        bool | None
    ) = None

    email_enabled: (
        bool | None
    ) = None

    push_enabled: (
        bool | None
    ) = None

    sound_enabled: (
        bool | None
    ) = None

    digest_enabled: (
        bool | None
    ) = None

    digest_hour: (
        int | None
    ) = Field(
        default=None,
        ge=0,
        le=23,
    )

    muted_types: (
        list[str] | None
    ) = None


# =========================================================
# INTERNAL CREATE CONTRACT
# =========================================================


class NotificationCreate(
    NotificationSchema
):
    recipient_user_id: uuid.UUID

    notification_type: str = Field(
        min_length=1,
        max_length=100,
    )

    title: str = Field(
        min_length=1,
        max_length=255,
    )

    body: (
        str | None
    ) = None

    priority: str = "normal"

    entity_type: (
        str | None
    ) = None

    entity_id: (
        uuid.UUID | None
    ) = None

    action_url: (
        str | None
    ) = None

    payload: dict = Field(
        default_factory=dict
    )


# =========================================================
# REALTIME EVENT CONTRACT
# =========================================================


class NotificationRealtimeEvent(
    NotificationSchema
):
    event: str

    workspace_id: uuid.UUID

    recipient_user_id: uuid.UUID

    notification: (
        NotificationResponse
        | None
    ) = None

    unread_count: int | None = None


__all__ = [
    "NotificationResponse",
    "NotificationListResponse",
    "NotificationUnreadCountResponse",
    "NotificationMutationResponse",
    "NotificationMarkAllReadResponse",
    "NotificationPreferenceResponse",
    "NotificationPreferenceUpdate",
    "NotificationCreate",
    "NotificationRealtimeEvent",
]