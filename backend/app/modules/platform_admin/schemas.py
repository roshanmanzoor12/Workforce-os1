from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PlatformTenantPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    status: str
    plan_code: str
    owner_email: str | None = None
    created_at: datetime
    updated_at: datetime


class PlatformTenantListResponse(BaseModel):
    items: list[PlatformTenantPublic]
    total: int


class PlatformTenantStatusUpdate(BaseModel):
    status: str = Field(
        ...,
        pattern=r"^(active|suspended)$",
    )


class PlatformSummaryResponse(BaseModel):
    tenant_count: int
    active_tenant_count: int
    suspended_tenant_count: int
    plan_counts: dict[str, int]
    generated_at: datetime