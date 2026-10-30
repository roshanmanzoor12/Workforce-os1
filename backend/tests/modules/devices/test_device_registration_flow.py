from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.modules.devices.credential_schemas import (
    DeviceRegistrationCredential,
)
from app.modules.devices.schemas import (
    DevicePublic,
    DeviceRegistrationRequest,
    DeviceRegistrationResponse,
)


# =========================================================
# CONSTANTS
# =========================================================

VALID_TEST_DEVICE_SECRET = (
    "wfds_test_device_secret_123456789"
)


# =========================================================
# HELPERS
# =========================================================


def utc_now() -> datetime:
    return datetime.now(
        timezone.utc
    )


def build_registration_request() -> DeviceRegistrationRequest:
    return DeviceRegistrationRequest(
        activation_code="wfdev_test_activation_code",
        hostname="WORKSTATION-01",
        os_name="Windows",
        os_version="11",
        architecture="x64",
        agent_version="0.1.0",
        agent_identifier="test-agent-001",
    )


def build_device_public() -> DevicePublic:
    device_id = uuid.uuid4()
    device_uuid = uuid.uuid4()
    now = utc_now()

    return DevicePublic(
        id=device_id,
        device_uuid=device_uuid,
        employee_id=None,
        hostname="WORKSTATION-01",
        os_name="Windows",
        os_version="11",
        architecture="x64",
        agent_version="0.1.0",
        agent_identifier="test-agent-001",
        status="active",
        is_active=True,
        first_seen_at=now,
        last_seen_at=now,
        registered_at=now,
        revoked_at=None,
        monitoring_profile_id=None,
        created_at=now,
        updated_at=now,
    )


def get_openapi_paths() -> set[str]:
    """
    FastAPI may keep included routers as lazy/internal router
    objects inside app.routes.

    OpenAPI is the stable public route contract for these tests.
    """

    from app.main import app

    schema = app.openapi()

    return set(
        schema.get(
            "paths",
            {}
        ).keys()
    )


# =========================================================
# REGISTRATION RESPONSE CONTRACT
# =========================================================


def test_registration_response_contains_one_time_credential() -> None:
    device = build_device_public()

    response = DeviceRegistrationResponse(
        message="Device registered.",
        device=device,
        credential=DeviceRegistrationCredential(
            device_uuid=device.device_uuid,
            device_secret=VALID_TEST_DEVICE_SECRET,
        ),
    )

    assert response.message == "Device registered."

    assert (
        response.device.device_uuid
        == device.device_uuid
    )

    assert (
        response.credential.device_uuid
        == device.device_uuid
    )

    assert (
        response.credential.device_secret
        == VALID_TEST_DEVICE_SECRET
    )


# =========================================================
# REGISTRATION REQUEST SECURITY CONTRACT
# =========================================================


def test_registration_request_does_not_accept_workspace_identity() -> None:
    with pytest.raises(
        Exception
    ):
        DeviceRegistrationRequest(
            activation_code="wfdev_test",
            hostname="WORKSTATION-01",
            os_name="Windows",
            agent_identifier="agent-001",
            workspace_id=uuid.uuid4(),
        )


def test_registration_request_does_not_accept_database_name() -> None:
    with pytest.raises(
        Exception
    ):
        DeviceRegistrationRequest(
            activation_code="wfdev_test",
            hostname="WORKSTATION-01",
            os_name="Windows",
            agent_identifier="agent-001",
            database_name="tenant_attacker_selected",
        )


def test_registration_request_does_not_accept_device_uuid() -> None:
    with pytest.raises(
        Exception
    ):
        DeviceRegistrationRequest(
            activation_code="wfdev_test",
            hostname="WORKSTATION-01",
            os_name="Windows",
            agent_identifier="agent-001",
            device_uuid=uuid.uuid4(),
        )


# =========================================================
# PUBLIC REGISTRATION ENDPOINT CONTRACT
# =========================================================


@pytest.mark.asyncio
async def test_registration_router_uses_registration_service() -> None:
    from app.modules.devices.registration_router import (
        register_device,
    )

    payload = build_registration_request()

    device = build_device_public()

    expected = DeviceRegistrationResponse(
        message="Device registered.",
        device=device,
        credential=DeviceRegistrationCredential(
            device_uuid=device.device_uuid,
            device_secret=VALID_TEST_DEVICE_SECRET,
        ),
    )

    service = MagicMock()

    service.register_device = AsyncMock(
        return_value=expected
    )

    result = await register_device(
        payload=payload,
        service=service,
    )

    service.register_device.assert_awaited_once_with(
        payload
    )

    assert result == expected


# =========================================================
# ROUTER REGISTRATION
# =========================================================


def test_main_registers_device_registration_route() -> None:
    paths = get_openapi_paths()

    assert (
        "/api/v1/device-registration/register"
        in paths
    )


def test_main_registers_device_agent_identity_route() -> None:
    paths = get_openapi_paths()

    assert (
        "/api/v1/device-agent/me"
        in paths
    )


# =========================================================
# AGENT RESPONSE SECURITY CONTRACT
# =========================================================


def test_agent_identity_response_exposes_only_safe_identity() -> None:
    from app.modules.devices.agent_schemas import (
        DeviceAgentIdentityResponse,
    )

    device_uuid = uuid.uuid4()

    response = DeviceAgentIdentityResponse(
        authenticated=True,
        device_uuid=device_uuid,
        credential_version=1,
    )

    serialized = response.model_dump()

    assert serialized == {
        "authenticated": True,
        "device_uuid": device_uuid,
        "credential_version": 1,
    }

    forbidden_fields = {
        "workspace_id",
        "database_name",
        "database_url",
        "cluster_key",
        "credential_id",
        "device_secret",
        "secret_hash",
    }

    assert (
        forbidden_fields.intersection(
            serialized.keys()
        )
        == set()
    )


# =========================================================
# DEVICE AUTH DEPENDENCY CONTRACT
# =========================================================


@pytest.mark.asyncio
async def test_invalid_device_uuid_returns_401() -> None:
    from fastapi import HTTPException

    from app.modules.devices.auth_dependency import (
        get_authenticated_device,
    )

    control_db = AsyncMock()

    with pytest.raises(
        HTTPException
    ) as exc_info:
        await get_authenticated_device(
            control_db=control_db,
            device_uuid_header="not-a-valid-uuid",
            device_secret_header=VALID_TEST_DEVICE_SECRET,
        )

    assert (
        exc_info.value.status_code
        == 401
    )

    assert (
        exc_info.value.detail
        == "Device authentication failed."
    )


# =========================================================
# AGENT AUTH SERVICE INVOCATION
# =========================================================


@pytest.mark.asyncio
async def test_auth_dependency_calls_device_auth_service() -> None:
    from app.modules.devices.auth_dependency import (
        get_authenticated_device,
    )
    from app.modules.devices.auth_service import (
        AuthenticatedDeviceContext,
    )

    device_uuid = uuid.uuid4()
    workspace_id = uuid.uuid4()
    device_id = uuid.uuid4()
    credential_id = uuid.uuid4()

    expected = AuthenticatedDeviceContext(
        workspace_id=workspace_id,
        device_id=device_id,
        device_uuid=device_uuid,
        credential_id=credential_id,
        credential_version=1,
        database_name=(
            f"tenant_{workspace_id.hex}"
        ),
        cluster_key="primary",
    )

    with patch(
        "app.modules.devices.auth_dependency.DeviceAuthService"
    ) as service_class:
        service = service_class.return_value

        service.authenticate_device = AsyncMock(
            return_value=expected
        )

        result = await get_authenticated_device(
            control_db=AsyncMock(),
            device_uuid_header=str(
                device_uuid
            ),
            device_secret_header=(
                VALID_TEST_DEVICE_SECRET
            ),
        )

    assert result == expected

    service.authenticate_device.assert_awaited_once()

    authentication_payload = (
        service.authenticate_device
        .await_args.args[0]
    )

    assert (
        authentication_payload.device_uuid
        == device_uuid
    )

    assert (
        authentication_payload.device_secret
        == VALID_TEST_DEVICE_SECRET
    )


# =========================================================
# DEVICE ROUTING SECURITY CONTRACT
# =========================================================


def test_resolved_device_route_does_not_contain_database_details() -> None:
    from app.modules.devices.routing_service import (
        ResolvedDeviceRoute,
    )

    route = ResolvedDeviceRoute(
        route_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        device_uuid=uuid.uuid4(),
        tenant_device_id=uuid.uuid4(),
    )

    assert not hasattr(
        route,
        "database_name",
    )

    assert not hasattr(
        route,
        "database_url",
    )

    assert not hasattr(
        route,
        "cluster_key",
    )


# =========================================================
# ROUTING SERVICE IDENTITY VALIDATION
# =========================================================


def test_routing_identity_validation_accepts_matching_route() -> None:
    from app.modules.devices.routing_service import (
        DeviceRoutingService,
        ResolvedDeviceRoute,
    )

    workspace_id = uuid.uuid4()
    device_uuid = uuid.uuid4()
    device_id = uuid.uuid4()

    route = ResolvedDeviceRoute(
        route_id=uuid.uuid4(),
        workspace_id=workspace_id,
        device_uuid=device_uuid,
        tenant_device_id=device_id,
    )

    DeviceRoutingService.validate_route_identity(
        route,
        expected_device_uuid=device_uuid,
        expected_workspace_id=workspace_id,
        expected_tenant_device_id=device_id,
    )


def test_routing_identity_validation_rejects_wrong_device() -> None:
    from app.core.exceptions import (
        ValidationError,
    )
    from app.modules.devices.routing_service import (
        DeviceRoutingService,
        ResolvedDeviceRoute,
    )

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


# =========================================================
# PUBLIC API MUST NOT ACCEPT TENANT ROUTING INPUT
# =========================================================


def test_registration_request_schema_has_no_tenant_routing_fields() -> None:
    schema_fields = set(
        DeviceRegistrationRequest.model_fields
    )

    forbidden = {
        "workspace_id",
        "tenant_id",
        "database_name",
        "database_url",
        "cluster_key",
        "device_uuid",
        "employee_id",
        "status",
        "monitoring_profile_id",
    }

    assert (
        schema_fields.intersection(
            forbidden
        )
        == set()
    )


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "VALID_TEST_DEVICE_SECRET",
    "utc_now",
    "build_registration_request",
    "build_device_public",
    "get_openapi_paths",
]