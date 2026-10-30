from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4


@dataclass(slots=True)
class PlatformTenant:
    id: UUID
    name: str
    slug: str
    status: str = "active"
    plan_code: str = "starter"
    owner_email: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        now = datetime.now(timezone.utc)

        if self.created_at is None:
            self.created_at = now

        if self.updated_at is None:
            self.updated_at = now


@dataclass(slots=True)
class PlatformSummary:
    tenant_count: int
    active_tenant_count: int
    suspended_tenant_count: int
    plan_counts: dict[str, int]
    generated_at: datetime