from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.modules.platform_admin.router import router
from app.modules.platform_admin.schemas import (
    PlatformTenantStatusUpdate,
)
from app.modules.platform_admin.service import (
    PlatformAdminService,
)


def test_platform_admin_router_is_registered() -> None:
    paths = {
        route.path
        for route in router.routes
    }

    assert "/platform-admin/tenants" in paths
    assert "/platform-admin/tenants/{tenant_id}" in paths
    assert "/platform-admin/tenants/{tenant_id}/status" in paths
    assert "/platform-admin/summary" in paths


def test_status_schema_accepts_active() -> None:
    payload = PlatformTenantStatusUpdate(
        status="active",
    )

    assert payload.status == "active"


def test_status_schema_rejects_invalid_status() -> None:
    with pytest.raises(ValueError):
        PlatformTenantStatusUpdate(
            status="deleted",
        )


@pytest.mark.asyncio
async def test_platform_admin_service_creates_and_suspends_tenant() -> None:
    service = PlatformAdminService()

    tenant = await service.create_tenant(
        name="Acme",
        slug="acme",
        plan_code="pro",
        owner_email="owner@example.com",
    )

    assert tenant.status == "active"
    assert tenant.slug == "acme"

    updated = await service.update_status(
        tenant_id=tenant.id,
        status="suspended",
    )

    assert updated.status == "suspended"


@pytest.mark.asyncio
async def test_platform_admin_summary() -> None:
    service = PlatformAdminService()

    await service.create_tenant(
        name="Acme",
        slug="acme",
        plan_code="pro",
        owner_email=None,
    )

    summary = await service.summary()

    assert summary.tenant_count == 1
    assert summary.active_tenant_count == 1
    assert summary.plan_counts["pro"] == 1