from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from app.modules.platform_admin.models import (
    PlatformSummary,
    PlatformTenant,
)
from app.modules.platform_admin.repository import (
    PlatformTenantRepository,
)


class PlatformTenantNotFoundError(LookupError):
    pass


class PlatformTenantValidationError(ValueError):
    pass


class PlatformAdminService:
    def __init__(
        self,
        repository: PlatformTenantRepository | None = None,
    ) -> None:
        self.repository = (
            repository
            if repository is not None
            else PlatformTenantRepository()
        )

    async def list_tenants(self) -> list[PlatformTenant]:
        return await self.repository.list()

    async def get_tenant(self, tenant_id: UUID) -> PlatformTenant:
        tenant = await self.repository.get(tenant_id)

        if tenant is None:
            raise PlatformTenantNotFoundError(
                f"Tenant {tenant_id} was not found."
            )

        return tenant

    async def create_tenant(
        self,
        *,
        name: str,
        slug: str,
        plan_code: str,
        owner_email: str | None,
    ) -> PlatformTenant:
        if not name.strip():
            raise PlatformTenantValidationError(
                "Tenant name is required."
            )

        if not slug.strip():
            raise PlatformTenantValidationError(
                "Tenant slug is required."
            )

        return await self.repository.seed(
            name=name.strip(),
            slug=slug.strip().lower(),
            plan_code=plan_code.strip().lower(),
            owner_email=owner_email,
        )

    async def update_status(
        self,
        tenant_id: UUID,
        status: str,
    ) -> PlatformTenant:
        if status not in {"active", "suspended"}:
            raise PlatformTenantValidationError(
                "Status must be active or suspended."
            )

        tenant = await self.get_tenant(tenant_id)
        tenant.status = status
        tenant.updated_at = datetime.now(timezone.utc)

        return await self.repository.save(tenant)

    async def summary(self) -> PlatformSummary:
        tenants = await self.repository.list()

        plan_counts: dict[str, int] = {}

        for tenant in tenants:
            plan_counts[tenant.plan_code] = (
                plan_counts.get(tenant.plan_code, 0) + 1
            )

        return PlatformSummary(
            tenant_count=len(tenants),
            active_tenant_count=sum(
                tenant.status == "active"
                for tenant in tenants
            ),
            suspended_tenant_count=sum(
                tenant.status == "suspended"
                for tenant in tenants
            ),
            plan_counts=plan_counts,
            generated_at=datetime.now(timezone.utc),
        )