from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.core.database import get_control_db
from app.modules.api_keys import authentication_dependency as dependency_module
from app.modules.api_keys.authentication import APIKeyPrincipal
from app.modules.api_keys.authentication_router import router


SECRET = "wfos_" + "a" * 32 + "." + "b" * 43


@pytest.fixture
def http_environment(monkeypatch):
    workspace_id = uuid4()

    registry = SimpleNamespace(
        database_name="tenant_" + workspace_id.hex,
        cluster_key="primary",
        schema_version="test_schema",
    )

    result = SimpleNamespace(
        scalar_one_or_none=lambda: registry
    )

    control = SimpleNamespace(
        execute=AsyncMock(return_value=result)
    )

    tenant = SimpleNamespace()

    entered_tenants = []

    @asynccontextmanager
    async def fake_tenant_session(
        database_name,
        *,
        cluster_key,
    ):
        entered_tenants.append(
            (database_name, cluster_key)
        )
        yield tenant

    verify_identity = AsyncMock()

    principal = APIKeyPrincipal(
        key_id=uuid4(),
        workspace_id=workspace_id,
        user_id=uuid4(),
        membership_id=uuid4(),
        scopes=frozenset({"employees.read"}),
    )

    authenticate = AsyncMock(return_value=principal)
    construction_arguments = []

    class FakeAuthentication:
        def __init__(self, **kwargs):
            construction_arguments.append(kwargs)

        async def authenticate(self, secret, *, required_scopes):
            return await authenticate(
                secret,
                required_scopes=required_scopes,
            )

    monkeypatch.setattr(
        dependency_module,
        "tenant_session",
        fake_tenant_session,
    )

    monkeypatch.setattr(
        dependency_module,
        "verify_tenant_identity",
        verify_identity,
    )

    monkeypatch.setattr(
        dependency_module,
        "APIKeyAuthentication",
        FakeAuthentication,
    )

    async def fake_control_db():
        yield control

    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[get_control_db] = fake_control_db

    return SimpleNamespace(
        app=app,
        client=TestClient(app),
        workspace_id=workspace_id,
        registry=registry,
        control=control,
        tenant=tenant,
        verify_identity=verify_identity,
        authenticate=authenticate,
        principal=principal,
        entered_tenants=entered_tenants,
        construction_arguments=construction_arguments,
        path=(
            "/api/v1/workspaces/"
            + str(workspace_id)
            + "/api-key-auth/context"
        ),
    )


def test_missing_header_returns_401_before_database_lookup(
    http_environment,
):
    env = http_environment

    response = env.client.get(env.path)

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "ApiKey"

    env.control.execute.assert_not_awaited()
    env.authenticate.assert_not_awaited()
    assert env.entered_tenants == []


def test_malformed_header_returns_401_before_database_lookup(
    http_environment,
):
    env = http_environment

    response = env.client.get(
        env.path,
        headers={"X-API-Key": "invalid"},
    )

    assert response.status_code == 401
    env.control.execute.assert_not_awaited()
    env.authenticate.assert_not_awaited()


def test_query_parameter_cannot_replace_header(
    http_environment,
):
    env = http_environment

    response = env.client.get(
        env.path,
        params={"X-API-Key": SECRET},
    )

    assert response.status_code == 401
    env.control.execute.assert_not_awaited()


def test_valid_header_dispatches_through_verified_tenant(
    http_environment,
):
    env = http_environment

    response = env.client.get(
        env.path,
        headers={"X-API-Key": SECRET},
    )

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"

    assert response.json() == {
        "key_id": str(env.principal.key_id),
        "workspace_id": str(env.workspace_id),
        "user_id": str(env.principal.user_id),
        "membership_id": str(env.principal.membership_id),
        "scopes": ["employees.read"],
    }

    assert env.entered_tenants == [
        (
            env.registry.database_name,
            env.registry.cluster_key,
        )
    ]

    env.verify_identity.assert_awaited_once()
    env.authenticate.assert_awaited_once_with(
        SECRET,
        required_scopes=frozenset(),
    )

    arguments = env.construction_arguments[0]

    assert arguments["workspace_id"] == env.workspace_id
    assert arguments["tenant_session"] is env.tenant
    assert arguments["control_session"] is env.control


def test_missing_registry_rejects_before_tenant_connection(
    http_environment,
):
    env = http_environment

    env.control.execute.return_value = SimpleNamespace(
        scalar_one_or_none=lambda: None
    )

    response = env.client.get(
        env.path,
        headers={"X-API-Key": SECRET},
    )

    assert response.status_code == 401
    assert env.entered_tenants == []
    env.authenticate.assert_not_awaited()


def test_failed_tenant_identity_prevents_authentication(
    http_environment,
):
    env = http_environment

    env.verify_identity.side_effect = RuntimeError(
        "Tenant identity mismatch"
    )

    with pytest.raises(
        RuntimeError,
        match="Tenant identity mismatch",
    ):
        env.client.get(
            env.path,
            headers={"X-API-Key": SECRET},
        )

    env.authenticate.assert_not_awaited()
    assert env.construction_arguments == []


@pytest.mark.parametrize("status_code", [401, 403])
def test_authentication_rejection_reaches_http_response(
    http_environment,
    status_code,
):
    env = http_environment

    env.authenticate.side_effect = HTTPException(
        status_code=status_code,
        detail="Authentication rejected.",
    )

    response = env.client.get(
        env.path,
        headers={"X-API-Key": SECRET},
    )

    assert response.status_code == status_code
    assert response.json() == {
        "detail": "Authentication rejected."
    }


def test_openapi_declares_header_authentication(
    http_environment,
):
    schema = http_environment.app.openapi()

    operation = schema["paths"][
        "/api/v1/workspaces/{workspace_id}/api-key-auth/context"
    ]["get"]

    assert {"WorkspaceAPIKey": []} in operation["security"]

    scheme = schema["components"]["securitySchemes"][
        "WorkspaceAPIKey"
    ]

    assert scheme["type"] == "apiKey"
    assert scheme["in"] == "header"
    assert scheme["name"] == "X-API-Key"


def test_authentication_endpoint_registered_in_main_application():
    from app.main import app

    schema = app.openapi()

    path = (
        "/api/v1/workspaces/{workspace_id}"
        "/api-key-auth/context"
    )

    assert path in schema["paths"]
    assert "get" in schema["paths"][path]

    operation = schema["paths"][path]["get"]

    assert {"WorkspaceAPIKey": []} in operation["security"]