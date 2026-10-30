from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from app.modules.knowledge.enums import (
    KnowledgeCategory,
    KnowledgeStatus,
    KnowledgeVisibility,
)


class KnowledgeSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True,
    )


class KnowledgeCreateRequest(
    KnowledgeSchema
):
    owner_employee_id: uuid.UUID

    title: str = Field(
        min_length=1,
        max_length=250,
    )

    content: str = Field(
        default="",
        max_length=200000,
    )

    category: KnowledgeCategory = (
        KnowledgeCategory.GENERAL
    )

    visibility: KnowledgeVisibility = (
        KnowledgeVisibility.PRIVATE
    )


class KnowledgeUpdateRequest(
    KnowledgeSchema
):
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=250,
    )

    content: str | None = Field(
        default=None,
        max_length=200000,
    )

    category: (
        KnowledgeCategory | None
    ) = None

    status: (
        KnowledgeStatus | None
    ) = None

    visibility: (
        KnowledgeVisibility | None
    ) = None


class KnowledgePublic(
    KnowledgeSchema
):
    id: uuid.UUID
    owner_employee_id: uuid.UUID

    title: str
    content: str

    category: KnowledgeCategory
    status: KnowledgeStatus
    visibility: KnowledgeVisibility

    created_at: datetime
    updated_at: datetime


class KnowledgeListResponse(
    KnowledgeSchema
):
    items: list[KnowledgePublic]

    total: int = Field(
        ge=0,
    )


__all__ = [
    "KnowledgeCreateRequest",
    "KnowledgeUpdateRequest",
    "KnowledgePublic",
    "KnowledgeListResponse",
]