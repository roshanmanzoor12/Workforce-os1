from __future__ import annotations

import inspect
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi.routing import APIRoute

from app.main import app
from app.modules.auth.permissions import get_current_verified_user
from app.modules.workspaces.provisioning import (
    WorkspaceProvisioningResult,
)
from app.modules.workspaces.provisioning_schemas import (
    WorkspaceProvisioningResponse,
    WorkspaceProvisioningRetryResponse,
)
from app.modules.workspaces.router import (
    provision_workspace,
    retry_workspace_provisioning,
    router as workspaces_router,
)


# =========================================================
# CONSTANTS
# =========================================================

WORKSPACE_ID = uuid.UUID(
    "11111111-1111-4111-8111-111111111111"
)

USER_ID = uuid.UUID(
    "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
)

DATABASE_NAME = (
    "tenant_11111111111141118111111111111111"
)

SCHEMA_VERSION = "2f8aa89ee8cc"

ROUTER_PROVISION_PATH = (
    "/workspaces/{workspace_id}/provision"
)

ROUTER_RETRY_PATH = (
    "/workspaces/{workspace_id}/retry-provisioning"
)

OPENAPI_PROVISION_PATH = (
    "/api/v1/workspaces/{workspace_id}/provision"
)

OPENAPI_RETRY_PATH = (
    "/api/v1/workspaces/{workspace_id}/retry-provisioning"
)


# =========================================================
# HELPERS
# =========================================================


def make_user() -> SimpleNamespace:
    return SimpleNamespace(
        id=USER_ID,
        email="owner@example.com",
    )


def make_result(
    *,
    database_created: bool = True,
    database_already_existed: bool = False,
    metadata_created: bool = True,
) -> WorkspaceProvisioningResult:
    return WorkspaceProvisioningResult(
        workspace_id=WORKSPACE_ID,
        database_name=DATABASE_NAME,
        cluster_key="primary",
        schema_version=SCHEMA_VERSION,
        database_created=database_created,
        database_already_existed=(
            database_already_existed
        ),
        metadata_created=metadata_created,
        workspace_ready=True,
        tenant_ready=True,
    )


def get_workspace_api_route(
    *,
    path: str,
    method: str,
) -> APIRoute:
    """
    Inspect the workspace APIRouter directly.

    FastAPI versions using lazy included routers may not flatten child
    APIRoute objects into app.routes immediately. The router itself is
    therefore the correct object for route/dependency introspection.

    Full /api/v1 registration is verified separately through OpenAPI.
    """

    for route in workspaces_router.routes:
        if not isinstance(
            route,
            APIRoute,
        ):
            continue

        if route.path != path:
            continue

        if method.upper() not in route.methods:
            continue

        return route

    raise AssertionError(
        f"Workspace route not found: {method} {path}"
    )


def dependency_contains_call(
    dependency,
    target,
) -> bool:
    if dependency.call is target:
        return True

    return any(
        dependency_contains_call(
            child,
            target,
        )
        for child in dependency.dependencies
    )


# =========================================================
# ROUTE REGISTRATION
# =========================================================


def test_provision_route_registered(
) -> None:
    route = get_workspace_api_route(
        path=ROUTER_PROVISION_PATH,
        method="POST",
    )

    assert route.status_code == 200

    assert (
        OPENAPI_PROVISION_PATH
        in app.openapi()["paths"]
    )


def test_retry_provisioning_route_registered(
) -> None:
    route = get_workspace_api_route(
        path=ROUTER_RETRY_PATH,
        method="POST",
    )

    assert route.status_code == 200

    assert (
        OPENAPI_RETRY_PATH
        in app.openapi()["paths"]
    )


# =========================================================
# VERIFIED AUTHENTICATION
# =========================================================


def test_provision_route_requires_verified_user(
) -> None:
    route = get_workspace_api_route(
        path=ROUTER_PROVISION_PATH,
        method="POST",
    )

    assert dependency_contains_call(
        route.dependant,
        get_current_verified_user,
    )


def test_retry_route_requires_verified_user(
) -> None:
    route = get_workspace_api_route(
        path=ROUTER_RETRY_PATH,
        method="POST",
    )

    assert dependency_contains_call(
        route.dependant,
        get_current_verified_user,
    )


# =========================================================
# CLIENT CANNOT CHOOSE DATABASE
# =========================================================


def test_provision_route_accepts_no_database_payload(
) -> None:
    signature = inspect.signature(
        provision_workspace
    )

    parameters = set(
        signature.parameters
    )

    assert "workspace_id" in parameters

    assert "database_name" not in parameters
    assert "database_url" not in parameters
    assert "cluster_key" not in parameters
    assert "payload" not in parameters


def test_retry_route_accepts_no_database_payload(
) -> None:
    signature = inspect.signature(
        retry_workspace_provisioning
    )

    parameters = set(
        signature.parameters
    )

    assert "workspace_id" in parameters

    assert "database_name" not in parameters
    assert "database_url" not in parameters
    assert "cluster_key" not in parameters
    assert "payload" not in parameters


def test_openapi_provision_endpoint_has_no_request_body(
) -> None:
    operation = (
        app.openapi()["paths"]
        [OPENAPI_PROVISION_PATH]
        ["post"]
    )

    assert "requestBody" not in operation


def test_openapi_retry_endpoint_has_no_request_body(
) -> None:
    operation = (
        app.openapi()["paths"]
        [OPENAPI_RETRY_PATH]
        ["post"]
    )

    assert "requestBody" not in operation


# =========================================================
# PUBLIC RESPONSE SECURITY
# =========================================================


def test_provisioning_response_does_not_expose_database_identity(
) -> None:
    fields = set(
        WorkspaceProvisioningResponse.model_fields
    )

    assert "database_name" not in fields
    assert "database_url" not in fields
    assert "host" not in fields
    assert "port" not in fields
    assert "username" not in fields
    assert "password" not in fields


def test_retry_response_does_not_expose_database_identity(
) -> None:
    fields = set(
        WorkspaceProvisioningRetryResponse.model_fields
    )

    assert "database_name" not in fields
    assert "database_url" not in fields
    assert "host" not in fields
    assert "port" not in fields
    assert "username" not in fields
    assert "password" not in fields


# =========================================================
# PROVISION ROUTE
# =========================================================


@pytest.mark.asyncio
async def test_provision_route_calls_service_with_workspace_and_user(
) -> None:
    user = make_user()

    service = SimpleNamespace(
        provision_workspace=AsyncMock(
            return_value=make_result()
        )
    )

    response = await provision_workspace(
        workspace_id=WORKSPACE_ID,
        workspace_service=service,
        current_user=user,
    )

    service.provision_workspace.assert_awaited_once_with(
        workspace_id=WORKSPACE_ID,
        user=user,
    )

    assert isinstance(
        response,
        WorkspaceProvisioningResponse,
    )

    assert response.workspace_id == WORKSPACE_ID
    assert response.cluster_key == "primary"
    assert response.schema_version == SCHEMA_VERSION

    assert response.database_created is True

    assert (
        response.database_already_existed
        is False
    )

    assert response.metadata_created is True
    assert response.workspace_ready is True
    assert response.tenant_ready is True


@pytest.mark.asyncio
async def test_provision_route_filters_internal_database_name(
) -> None:
    user = make_user()

    service = SimpleNamespace(
        provision_workspace=AsyncMock(
            return_value=make_result()
        )
    )

    response = await provision_workspace(
        workspace_id=WORKSPACE_ID,
        workspace_service=service,
        current_user=user,
    )

    serialized = response.model_dump()

    assert "database_name" not in serialized
    assert "database_url" not in serialized

    assert DATABASE_NAME not in str(
        serialized
    )


# =========================================================
# RETRY ROUTE
# =========================================================


@pytest.mark.asyncio
async def test_retry_route_calls_retry_service_path(
) -> None:
    user = make_user()

    service = SimpleNamespace(
        retry_workspace_provisioning=AsyncMock(
            return_value=make_result(
                database_created=False,
                database_already_existed=True,
                metadata_created=False,
            )
        )
    )

    response = (
        await retry_workspace_provisioning(
            workspace_id=WORKSPACE_ID,
            workspace_service=service,
            current_user=user,
        )
    )

    (
        service.retry_workspace_provisioning
        .assert_awaited_once_with(
            workspace_id=WORKSPACE_ID,
            user=user,
        )
    )

    assert isinstance(
        response,
        WorkspaceProvisioningRetryResponse,
    )

    assert response.workspace_id == WORKSPACE_ID

    assert response.database_created is False

    assert (
        response.database_already_existed
        is True
    )

    assert response.metadata_created is False
    assert response.workspace_ready is True
    assert response.tenant_ready is True
    assert response.retried is True


@pytest.mark.asyncio
async def test_retry_route_filters_internal_database_name(
) -> None:
    user = make_user()

    service = SimpleNamespace(
        retry_workspace_provisioning=AsyncMock(
            return_value=make_result(
                database_created=False,
                database_already_existed=True,
                metadata_created=False,
            )
        )
    )

    response = (
        await retry_workspace_provisioning(
            workspace_id=WORKSPACE_ID,
            workspace_service=service,
            current_user=user,
        )
    )

    serialized = response.model_dump()

    assert "database_name" not in serialized
    assert "database_url" not in serialized

    assert DATABASE_NAME not in str(
        serialized
    )


# =========================================================
# SERVICE ERROR PROPAGATION
# =========================================================


@pytest.mark.asyncio
async def test_provision_route_does_not_hide_service_failure(
) -> None:
    user = make_user()

    error = RuntimeError(
        "simulated provisioning failure"
    )

    service = SimpleNamespace(
        provision_workspace=AsyncMock(
            side_effect=error
        )
    )

    with pytest.raises(
        RuntimeError,
        match="simulated provisioning failure",
    ):
        await provision_workspace(
            workspace_id=WORKSPACE_ID,
            workspace_service=service,
            current_user=user,
        )


@pytest.mark.asyncio
async def test_retry_route_does_not_hide_service_failure(
) -> None:
    user = make_user()

    error = RuntimeError(
        "simulated retry failure"
    )

    service = SimpleNamespace(
        retry_workspace_provisioning=AsyncMock(
            side_effect=error
        )
    )

    with pytest.raises(
        RuntimeError,
        match="simulated retry failure",
    ):
        await retry_workspace_provisioning(
            workspace_id=WORKSPACE_ID,
            workspace_service=service,
            current_user=user,
        )


# =========================================================
# OPENAPI RESPONSE CONTRACT
# =========================================================


def test_provision_openapi_response_has_public_schema(
) -> None:
    operation = (
        app.openapi()["paths"]
        [OPENAPI_PROVISION_PATH]
        ["post"]
    )

    response = (
        operation["responses"]["200"]
    )

    schema = (
        response["content"]
        ["application/json"]
        ["schema"]
    )

    reference = schema.get(
        "$ref",
        "",
    )

    assert (
        "WorkspaceProvisioningResponse"
        in reference
    )


def test_retry_openapi_response_has_public_schema(
) -> None:
    operation = (
        app.openapi()["paths"]
        [OPENAPI_RETRY_PATH]
        ["post"]
    )

    response = (
        operation["responses"]["200"]
    )

    schema = (
        response["content"]
        ["application/json"]
        ["schema"]
    )

    reference = schema.get(
        "$ref",
        "",
    )

    assert (
        "WorkspaceProvisioningRetryResponse"
        in reference
    )