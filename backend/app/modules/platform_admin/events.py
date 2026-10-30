from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID


@dataclass(frozen=True, slots=True)
class PlatformTenantStatusChanged:
    tenant_id: UUID
    status: str
    occurred_at: datetime

    @classmethod
    def create(
        cls,
        *,
        tenant_id: UUID,
        status: str,
    ) -> "PlatformTenantStatusChanged":
        return cls(
            tenant_id=tenant_id,
            status=status,
            occurred_at=datetime.now(timezone.utc),
        )