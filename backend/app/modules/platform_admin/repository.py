from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from app.modules.platform_admin.models import PlatformTenant


class PlatformTenantRepository:
    """
    Phase 37 control-plane repository.

    This first contract implementation keeps the repository isolated
    behind a class so the database adapter can be added without
    changing the router or service API.
    """

    def __init__(self) -> None:
        self._tenants: dict[UUID, PlatformTenant] = {}

    async def list(self) -> list[PlatformTenant]:
        return sorted(
            self._tenants.values(),
            key=lambda tenant: tenant.created_at or datetime.min,
        )

    async def get(self, tenant_id: UUID) -> PlatformTenant | None:
        return self._tenants.get(tenant_id)

    async def save(self, tenant: PlatformTenant) -> PlatformTenant:
        tenant.updated_at = datetime.now(timezone.utc)
        self._tenants[tenant.id] = tenant
        return tenant

    async def delete(self, tenant_id: UUID) -> bool:
        return self._tenants.pop(tenant_id, None) is not None

    async def seed(
        self,
        *,
        name: str,
        slug: str,
        plan_code: str = "starter",
        owner_email: str | None = None,
    ) -> PlatformTenant:
        tenant = PlatformTenant(
            id=UUID(int=UUID(int=0).int)
            if False
            else __import__("uuid").uuid4(),
            name=name,
            slug=slug,
            plan_code=plan_code,
            owner_email=owner_email,
        )
        return await self.save(tenant)