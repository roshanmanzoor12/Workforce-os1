from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class AuditSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True,
    )


class AuditEventCreate(
    AuditSchema
):
    actor_user_id: (
        uuid.UUID | None
    ) = None

    category: str = Field(
        min_length=1,
        max_length=100,
    )

    action: str = Field(
        min_length=1,
        max_length=150,
    )

    outcome: str = "success"

    severity: str = "info"

    target_type: (
        str | None
    ) = Field(
        default=None,
        max_length=100,
    )

    target_id: (
        uuid.UUID | None
    ) = None

    target_label: (
        str | None
    ) = Field(
        default=None,
        max_length=255,
    )

    message: (
        str | None
    ) = None

    request_id: (
        str | None
    ) = Field(
        default=None,
        max_length=100,
    )

    ip_address: (
        str | None
    ) = Field(
        default=None,
        max_length=64,
    )

    user_agent: (
        str | None
    ) = Field(
        default=None,
        max_length=1000,
    )

    event_data: dict = Field(
        default_factory=dict
    )


class AuditEventResponse(
    AuditSchema
):
    id: uuid.UUID

    workspace_id: uuid.UUID

    actor_user_id: (
        uuid.UUID | None
    )

    category: str

    action: str

    outcome: str

    severity: str

    target_type: str | None

    target_id: uuid.UUID | None

    target_label: str | None

    message: str | None

    request_id: str | None

    ip_address: str | None

    user_agent: str | None

    event_data: dict

    occurred_at: datetime


class AuditEventListResponse(
    AuditSchema
):
    items: list[
        AuditEventResponse
    ] = Field(
        default_factory=list
    )

    total: int

    limit: int

    offset: int


class AuditCapabilitiesResponse(
    AuditSchema
):
    append_only: bool = True

    update_supported: bool = False

    delete_supported: bool = False

    filters: list[str] = Field(
        default_factory=lambda: [
            "category",
            "action",
            "actor_user_id",
            "target_type",
            "target_id",
            "outcome",
            "severity",
            "start_at",
            "end_at",
        ]
    )


__all__ = [
    "AuditEventCreate",
    "AuditEventResponse",
    "AuditEventListResponse",
    "AuditCapabilitiesResponse",
]