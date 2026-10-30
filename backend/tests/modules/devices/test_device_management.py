from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import (
    AsyncMock,
    MagicMock,
    patch,
)

import pytest

from app.core.exceptions import (
    ResourceNotFound,
    ValidationError,
)
from app.modules.devices.management_service import (
    DeviceManagementService,
)
from app.modules.devices.schemas import (
    DeviceDeleteResponse,
)


# =========================================================
# CONSTANTS
# =========================================================

READY_TENANT_STATUS = "ready"


# =========================================================
# HELPERS
# =========================================================


def build_registry(
    *,
    workspace_id: uuid.UUID | None = None,
    database_name: str | None = None,
    cluster_key: str = "primary",
    status: str = READY_TENANT_STATUS,
):
    workspace_id = (
        workspace_id
        or uuid.uuid4()
    )

    return SimpleNamespace(
        workspace_id=workspace_id,
        database_name=(
            database_name
            or f"tenant_{workspace_id.hex}"
        ),
        cluster_key=cluster_key,
        status=status,
    )


def build_route(
    *,
    workspace_id: uuid.UUID | None = None,
    device_uuid: uuid.UUID | None = None,
    tenant_device_id: uuid.UUID | None = None,
):
    return SimpleNamespace(
        route_id=uuid.uuid4(),
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
    )


def build_device_detail(
    *,
    device_id: uuid.UUID,
    device_uuid: uuid.UUID,
):
    return SimpleNamespace(
        device=SimpleNamespace(
            id=device_id,
            device_uuid=device_uuid,
        )
    )


def build_execute_result(
    value,
) -> MagicMock:
    result = MagicMock()

    result.scalar_one_or_none.return_value = (
        value
    )

    return result


# =========================================================
# REGISTRY LOOKUP
# =========================================================


@pytest.mark.asyncio
async def test_require_ready_registry_rejects_missing_registry() -> None:
    control_session = AsyncMock()

    service = DeviceManagementService(
        control_session
    )

    control_session.execute.return_value = (
        build_execute_result(
            None
        )
    )

    with pytest.raises(
        ResourceNotFound
    ):
        await service._require_ready_registry(
            workspace_id=uuid.uuid4()
        )

    control_session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_require_ready_registry_rejects_non_ready_registry() -> None:
    control_session = AsyncMock()

    service = DeviceManagementService(
        control_session
    )

    workspace_id = uuid.uuid4()

    registry = build_registry(
        workspace_id=workspace_id,
        status="provisioning",
    )

    control_session.execute.return_value = (
        build_execute_result(
            registry
        )
    )

    with pytest.raises(
        ValidationError
    ):
        await service._require_ready_registry(
            workspace_id=workspace_id
        )

    control_session.execute.assert_awaited_once()


# =========================================================
# ROUTE IDENTITY CHECKS
# =========================================================


@pytest.mark.asyncio
async def test_revoke_device_rejects_wrong_workspace_route() -> None:
    control_session = AsyncMock()

    service = DeviceManagementService(
        control_session
    )

    workspace_id = uuid.uuid4()
    device_id = uuid.uuid4()
    device_uuid = uuid.uuid4()

    registry = build_registry(
        workspace_id=workspace_id
    )

    service._require_ready_registry = AsyncMock(
        return_value=registry
    )

    service.routing_service.resolve_device_route = AsyncMock(
        return_value=build_route(
            workspace_id=uuid.uuid4(),
            device_uuid=device_uuid,
            tenant_device_id=device_id,
        )
    )

    with pytest.raises(
        ResourceNotFound
    ):
        await service.revoke_device(
            workspace_id=workspace_id,
            device_id=device_id,
            device_uuid=device_uuid,
        )


@pytest.mark.asyncio
async def test_revoke_device_rejects_wrong_tenant_device_route() -> None:
    control_session = AsyncMock()

    service = DeviceManagementService(
        control_session
    )

    workspace_id = uuid.uuid4()
    device_id = uuid.uuid4()
    device_uuid = uuid.uuid4()

    registry = build_registry(
        workspace_id=workspace_id
    )

    service._require_ready_registry = AsyncMock(
        return_value=registry
    )

    service.routing_service.resolve_device_route = AsyncMock(
        return_value=build_route(
            workspace_id=workspace_id,
            device_uuid=device_uuid,
            tenant_device_id=uuid.uuid4(),
        )
    )

    with pytest.raises(
        ResourceNotFound
    ):
        await service.revoke_device(
            workspace_id=workspace_id,
            device_id=device_id,
            device_uuid=device_uuid,
        )


# =========================================================
# TENANT DEVICE IDENTITY
# =========================================================


@pytest.mark.asyncio
async def test_revoke_device_rejects_tenant_uuid_mismatch() -> None:
    control_session = AsyncMock()

    service = DeviceManagementService(
        control_session
    )

    workspace_id = uuid.uuid4()
    device_id = uuid.uuid4()
    device_uuid = uuid.uuid4()

    registry = build_registry(
        workspace_id=workspace_id
    )

    service._require_ready_registry = AsyncMock(
        return_value=registry
    )

    service.routing_service.resolve_device_route = AsyncMock(
        return_value=build_route(
            workspace_id=workspace_id,
            device_uuid=device_uuid,
            tenant_device_id=device_id,
        )
    )

    service.routing_service.revoke_route = AsyncMock()

    tenant_session_mock = AsyncMock()

    tenant_context = AsyncMock()
    tenant_context.__aenter__.return_value = (
        tenant_session_mock
    )
    tenant_context.__aexit__.return_value = False

    wrong_uuid = uuid.uuid4()

    with (
        patch(
            "app.modules.devices.management_service.tenant_session",
            return_value=tenant_context,
        ),
        patch(
            "app.modules.devices.management_service.DeviceService"
        ) as device_service_class,
    ):
        service._verify_tenant_identity = AsyncMock()

        device_service = (
            device_service_class.return_value
        )

        device_service.get_device = AsyncMock(
            return_value=build_device_detail(
                device_id=device_id,
                device_uuid=wrong_uuid,
            )
        )

        with pytest.raises(
            ResourceNotFound
        ):
            await service.revoke_device(
                workspace_id=workspace_id,
                device_id=device_id,
                device_uuid=device_uuid,
            )

    service.routing_service.revoke_route.assert_not_awaited()


# =========================================================
# SUCCESSFUL CROSS-PLANE REVOKE
# =========================================================


@pytest.mark.asyncio
async def test_revoke_device_revokes_tenant_then_control_route() -> None:
    control_session = AsyncMock()

    service = DeviceManagementService(
        control_session
    )

    workspace_id = uuid.uuid4()
    device_id = uuid.uuid4()
    device_uuid = uuid.uuid4()

    registry = build_registry(
        workspace_id=workspace_id
    )

    route = build_route(
        workspace_id=workspace_id,
        device_uuid=device_uuid,
        tenant_device_id=device_id,
    )

    service._require_ready_registry = AsyncMock(
        return_value=registry
    )

    service.routing_service.resolve_device_route = AsyncMock(
        return_value=route
    )

    service.routing_service.revoke_route = AsyncMock()

    tenant_session_mock = AsyncMock()

    tenant_context = AsyncMock()
    tenant_context.__aenter__.return_value = (
        tenant_session_mock
    )
    tenant_context.__aexit__.return_value = False

    expected_result = DeviceDeleteResponse(
        message="Device revoked.",
        success=True,
    )

    with (
        patch(
            "app.modules.devices.management_service.tenant_session",
            return_value=tenant_context,
        ),
        patch(
            "app.modules.devices.management_service.DeviceService"
        ) as device_service_class,
    ):
        service._verify_tenant_identity = AsyncMock()

        device_service = (
            device_service_class.return_value
        )

        device_service.get_device = AsyncMock(
            return_value=build_device_detail(
                device_id=device_id,
                device_uuid=device_uuid,
            )
        )

        device_service.revoke_device = AsyncMock(
            return_value=expected_result
        )

        result = await service.revoke_device(
            workspace_id=workspace_id,
            device_id=device_id,
            device_uuid=device_uuid,
        )

    assert result == expected_result

    service._require_ready_registry.assert_awaited_once_with(
        workspace_id=workspace_id
    )

    service.routing_service.resolve_device_route.assert_awaited_once_with(
        device_uuid=device_uuid
    )

    service._verify_tenant_identity.assert_awaited_once_with(
        tenant_session_mock,
        workspace_id=workspace_id,
    )

    device_service.get_device.assert_awaited_once_with(
        device_id=device_id
    )

    device_service.revoke_device.assert_awaited_once_with(
        device_id=device_id
    )

    service.routing_service.revoke_route.assert_awaited_once_with(
        device_uuid=device_uuid
    )


# =========================================================
# CONTROL ROUTE FAILURE
# =========================================================


@pytest.mark.asyncio
async def test_tenant_revocation_remains_when_route_revocation_fails() -> None:
    control_session = AsyncMock()

    service = DeviceManagementService(
        control_session
    )

    workspace_id = uuid.uuid4()
    device_id = uuid.uuid4()
    device_uuid = uuid.uuid4()

    registry = build_registry(
        workspace_id=workspace_id
    )

    route = build_route(
        workspace_id=workspace_id,
        device_uuid=device_uuid,
        tenant_device_id=device_id,
    )

    service._require_ready_registry = AsyncMock(
        return_value=registry
    )

    service.routing_service.resolve_device_route = AsyncMock(
        return_value=route
    )

    service.routing_service.revoke_route = AsyncMock(
        side_effect=RuntimeError(
            "control route failure"
        )
    )

    tenant_session_mock = AsyncMock()

    tenant_context = AsyncMock()
    tenant_context.__aenter__.return_value = (
        tenant_session_mock
    )
    tenant_context.__aexit__.return_value = False

    with (
        patch(
            "app.modules.devices.management_service.tenant_session",
            return_value=tenant_context,
        ),
        patch(
            "app.modules.devices.management_service.DeviceService"
        ) as device_service_class,
    ):
        service._verify_tenant_identity = AsyncMock()

        device_service = (
            device_service_class.return_value
        )

        device_service.get_device = AsyncMock(
            return_value=build_device_detail(
                device_id=device_id,
                device_uuid=device_uuid,
            )
        )

        device_service.revoke_device = AsyncMock(
            return_value=DeviceDeleteResponse(
                message="Device revoked.",
                success=True,
            )
        )

        with pytest.raises(
            RuntimeError,
            match="control route failure",
        ):
            await service.revoke_device(
                workspace_id=workspace_id,
                device_id=device_id,
                device_uuid=device_uuid,
            )

    device_service.revoke_device.assert_awaited_once_with(
        device_id=device_id
    )

    service.routing_service.revoke_route.assert_awaited_once_with(
        device_uuid=device_uuid
    )


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "READY_TENANT_STATUS",
    "build_registry",
    "build_route",
    "build_device_detail",
    "build_execute_result",
]