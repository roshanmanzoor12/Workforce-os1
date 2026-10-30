from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import (
    ConflictError,
    ResourceNotFound,
    ValidationError,
)
from app.modules.devices.routing_models import (
    DEVICE_ROUTE_STATUS_ACTIVE,
    DEVICE_ROUTE_STATUS_REVOKED,
)
from app.modules.devices.routing_service import (
    DeviceRoutingService,
    ResolvedDeviceRoute,
)


# =========================================================
# HELPERS
# =========================================================


def utc_now() -> datetime:
    return datetime.now(
        timezone.utc
    )


def build_route(
    *,
    route_id: uuid.UUID | None = None,
    workspace_id: uuid.UUID | None = None,
    device_uuid: uuid.UUID | None = None,
    tenant_device_id: uuid.UUID | None = None,
    status: str = DEVICE_ROUTE_STATUS_ACTIVE,
    is_active: bool = True,
):
    return SimpleNamespace(
        id=route_id or uuid.uuid4(),
        workspace_id=(
            workspace_id
            or uuid.uuid4()
        ),
        device_uuid=(
            device_uuid
            or uuid.uuid4()
        ),
        tenant_device_id=(
            tenant_device_id
            or uuid.uuid4()
        ),
        status=status,
        is_active=is_active,
        registered_at=utc_now(),
        revoked_at=None,
        created_at=utc_now(),
        updated_at=utc_now(),
    )


# =========================================================
# CREATE ROUTE
# =========================================================


@pytest.mark.asyncio
async def test_create_route_rejects_duplicate_device_uuid() -> None:
    session = AsyncMock()

    service = DeviceRoutingService(
        session
    )

    existing = build_route()

    service.repository.get_by_device_uuid = AsyncMock(
        return_value=existing
    )

    with pytest.raises(
        ConflictError
    ):
        await service.create_route(
            workspace_id=uuid.uuid4(),
            device_uuid=existing.device_uuid,
            tenant_device_id=uuid.uuid4(),
        )

    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_route_rejects_duplicate_tenant_device() -> None:
    session = AsyncMock()

    service = DeviceRoutingService(
        session
    )

    workspace_id = uuid.uuid4()
    tenant_device_id = uuid.uuid4()

    service.repository.get_by_device_uuid = AsyncMock(
        return_value=None
    )

    service.repository.get_workspace_device_route = AsyncMock(
        return_value=build_route(
            workspace_id=workspace_id,
            tenant_device_id=tenant_device_id,
        )
    )

    with pytest.raises(
        ConflictError
    ):
        await service.create_route(
            workspace_id=workspace_id,
            device_uuid=uuid.uuid4(),
            tenant_device_id=tenant_device_id,
        )

    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_route_commits_new_route() -> None:
    session = AsyncMock()

    service = DeviceRoutingService(
        session
    )

    workspace_id = uuid.uuid4()
    device_uuid = uuid.uuid4()
    tenant_device_id = uuid.uuid4()

    route = build_route(
        workspace_id=workspace_id,
        device_uuid=device_uuid,
        tenant_device_id=tenant_device_id,
    )

    service.repository.get_by_device_uuid = AsyncMock(
        return_value=None
    )

    service.repository.get_workspace_device_route = AsyncMock(
        return_value=None
    )

    service.repository.create_route = AsyncMock(
        return_value=route
    )

    result = await service.create_route(
        workspace_id=workspace_id,
        device_uuid=device_uuid,
        tenant_device_id=tenant_device_id,
    )

    assert result is route

    service.repository.create_route.assert_awaited_once_with(
        workspace_id=workspace_id,
        device_uuid=device_uuid,
        tenant_device_id=tenant_device_id,
        status=DEVICE_ROUTE_STATUS_ACTIVE,
        is_active=True,
        registered_at=(
            service.repository.create_route
            .await_args.kwargs[
                "registered_at"
            ]
        ),
    )

    session.commit.assert_awaited_once()

    session.refresh.assert_awaited_once_with(
        route
    )


# =========================================================
# RESOLVE ROUTE
# =========================================================


@pytest.mark.asyncio
async def test_resolve_route_rejects_unknown_device() -> None:
    session = AsyncMock()

    service = DeviceRoutingService(
        session
    )

    service.repository.get_active_by_device_uuid = AsyncMock(
        return_value=None
    )

    with pytest.raises(
        ResourceNotFound
    ):
        await service.resolve_device_route(
            device_uuid=uuid.uuid4()
        )


@pytest.mark.asyncio
async def test_resolve_route_rejects_non_active_status() -> None:
    session = AsyncMock()

    service = DeviceRoutingService(
        session
    )

    route = build_route(
        status=DEVICE_ROUTE_STATUS_REVOKED,
        is_active=True,
    )

    service.repository.get_active_by_device_uuid = AsyncMock(
        return_value=route
    )

    with pytest.raises(
        ResourceNotFound
    ):
        await service.resolve_device_route(
            device_uuid=route.device_uuid
        )


@pytest.mark.asyncio
async def test_resolve_route_rejects_inactive_route() -> None:
    session = AsyncMock()

    service = DeviceRoutingService(
        session
    )

    route = build_route(
        status=DEVICE_ROUTE_STATUS_ACTIVE,
        is_active=False,
    )

    service.repository.get_active_by_device_uuid = AsyncMock(
        return_value=route
    )

    with pytest.raises(
        ResourceNotFound
    ):
        await service.resolve_device_route(
            device_uuid=route.device_uuid
        )


@pytest.mark.asyncio
async def test_resolve_route_returns_safe_identity() -> None:
    session = AsyncMock()

    service = DeviceRoutingService(
        session
    )

    route = build_route()

    service.repository.get_active_by_device_uuid = AsyncMock(
        return_value=route
    )

    result = await service.resolve_device_route(
        device_uuid=route.device_uuid
    )

    assert isinstance(
        result,
        ResolvedDeviceRoute,
    )

    assert result.route_id == route.id
    assert result.workspace_id == route.workspace_id
    assert result.device_uuid == route.device_uuid
    assert result.tenant_device_id == route.tenant_device_id

    assert not hasattr(
        result,
        "database_name",
    )

    assert not hasattr(
        result,
        "database_url",
    )

    assert not hasattr(
        result,
        "cluster_key",
    )


# =========================================================
# REVOKE ROUTE
# =========================================================


@pytest.mark.asyncio
async def test_revoke_route_is_idempotent_when_missing() -> None:
    session = AsyncMock()

    service = DeviceRoutingService(
        session
    )

    service.repository.get_by_device_uuid_for_update = AsyncMock(
        return_value=None
    )

    await service.revoke_route(
        device_uuid=uuid.uuid4()
    )

    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_revoke_route_is_idempotent_when_already_revoked() -> None:
    session = AsyncMock()

    service = DeviceRoutingService(
        session
    )

    route = build_route(
        status=DEVICE_ROUTE_STATUS_REVOKED,
        is_active=False,
    )

    service.repository.get_by_device_uuid_for_update = AsyncMock(
        return_value=route
    )

    await service.revoke_route(
        device_uuid=route.device_uuid
    )

    service.repository.revoke_route.assert_not_awaited()

    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_revoke_route_is_idempotent_when_already_revoked() -> None:
    session = AsyncMock()

    service = DeviceRoutingService(
        session
    )

    route = build_route(
        status=DEVICE_ROUTE_STATUS_REVOKED,
        is_active=False,
    )

    service.repository.get_by_device_uuid_for_update = AsyncMock(
        return_value=route
    )

    service.repository.revoke_route = AsyncMock()

    await service.revoke_route(
        device_uuid=route.device_uuid
    )

    service.repository.get_by_device_uuid_for_update.assert_awaited_once_with(
        route.device_uuid
    )

    service.repository.revoke_route.assert_not_awaited()

    session.commit.assert_not_awaited()


# =========================================================
# IDENTITY VALIDATION
# =========================================================


def test_validate_route_identity_accepts_matching_values() -> None:
    workspace_id = uuid.uuid4()
    device_uuid = uuid.uuid4()
    tenant_device_id = uuid.uuid4()

    route = ResolvedDeviceRoute(
        route_id=uuid.uuid4(),
        workspace_id=workspace_id,
        device_uuid=device_uuid,
        tenant_device_id=tenant_device_id,
    )

    DeviceRoutingService.validate_route_identity(
        route,
        expected_device_uuid=device_uuid,
        expected_workspace_id=workspace_id,
        expected_tenant_device_id=tenant_device_id,
    )


def test_validate_route_identity_rejects_device_uuid_mismatch() -> None:
    route = ResolvedDeviceRoute(
        route_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        device_uuid=uuid.uuid4(),
        tenant_device_id=uuid.uuid4(),
    )

    with pytest.raises(
        ValidationError
    ):
        DeviceRoutingService.validate_route_identity(
            route,
            expected_device_uuid=uuid.uuid4(),
        )


def test_validate_route_identity_rejects_workspace_mismatch() -> None:
    route = ResolvedDeviceRoute(
        route_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        device_uuid=uuid.uuid4(),
        tenant_device_id=uuid.uuid4(),
    )

    with pytest.raises(
        ValidationError
    ):
        DeviceRoutingService.validate_route_identity(
            route,
            expected_device_uuid=route.device_uuid,
            expected_workspace_id=uuid.uuid4(),
        )


def test_validate_route_identity_rejects_tenant_device_mismatch() -> None:
    route = ResolvedDeviceRoute(
        route_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        device_uuid=uuid.uuid4(),
        tenant_device_id=uuid.uuid4(),
    )

    with pytest.raises(
        ValidationError
    ):
        DeviceRoutingService.validate_route_identity(
            route,
            expected_device_uuid=route.device_uuid,
            expected_tenant_device_id=uuid.uuid4(),
        )


# =========================================================
# STATUS CONTRACT
# =========================================================


def test_route_status_constants_are_distinct() -> None:
    assert (
        DEVICE_ROUTE_STATUS_ACTIVE
        != DEVICE_ROUTE_STATUS_REVOKED
    )


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "utc_now",
    "build_route",
]