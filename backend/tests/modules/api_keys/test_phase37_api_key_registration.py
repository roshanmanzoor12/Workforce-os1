from __future__ import annotations

import importlib
from uuid import UUID

import pytest
from fastapi import HTTPException
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from app.config import settings
from app.db.tenant_dependency import get_tenant_scope
from app.main import app
from app.modules.api_keys.schemas import APIKeyPublic


api_key_router_module = importlib.import_module(
    "app.modules.api_keys.router"
)

WORKSPACE_ID = UUID("34527ffb-e094-4e5e-89ee-4cab97244fc3")
KEY_ID = UUID("00000000-0000-4000-8000-000000000001")

DEPENDENCY_MARKER = "API_KEY_TENANT_DEPENDENCY_REACHED"


@pytest.mark.parametrize(
    ("method", "suffix", "endpoint_name"),
    [
        ("GET", "", "list_api_keys"),
        ("POST", "", "create_api_key"),
        ("GET", "/{key_id}", "get_api_key"),
        ("POST", "/{key_id}/revoke", "revoke_api_key"),
        ("POST", "/{key_id}/rotate", "rotate_api_key"),
    ],
)
def test_api_key_endpoint_registered_and_dispatches(
    monkeypatch: pytest.MonkeyPatch,
    method: str,
    suffix: str,
    endpoint_name: str,
) -> None:
    prefix = settings.api_v1_prefix.rstrip("/")
    schema_path = (
        prefix
        + "/workspaces/{workspace_id}/api-keys"
        + suffix
    )

    operation = (
        app.openapi()
        .get("paths", {})
        .get(schema_path, {})
        .get(method.lower())
    )

    assert operation is not None, (
        f"Missing OpenAPI operation: {method} {schema_path}"
    )

    local_path = (
        "/workspaces/{workspace_id}/api-keys"
        + suffix
    )

    matches = [
        route
        for route in api_key_router_module.router.routes
        if isinstance(route, APIRoute)
        and route.path == local_path
        and method in route.methods
    ]

    assert len(matches) == 1

    route = matches[0]

    assert route.endpoint is getattr(
        api_key_router_module,
        endpoint_name,
    )

    assert any(
        dependency.name == "scope"
        and dependency.call is get_tenant_scope
        for dependency in route.dependant.dependencies
    )

    dependency_calls: list[str] = []

    def stop_at_tenant_dependency() -> None:
        dependency_calls.append(DEPENDENCY_MARKER)
        raise HTTPException(
            status_code=418,
            detail=DEPENDENCY_MARKER,
        )

    monkeypatch.setattr(
        app,
        "dependency_overrides",
        {
            **app.dependency_overrides,
            get_tenant_scope: stop_at_tenant_dependency,
        },
    )

    request_path = (
        schema_path
        .replace("{workspace_id}", str(WORKSPACE_ID))
        .replace("{key_id}", str(KEY_ID))
    )

    request_options = {}

    if endpoint_name == "create_api_key":
        request_options["json"] = {
            "name": "Registration test",
            "scopes": ["employees.read"],
        }

    # Exercise routing without starting application lifespan
    # or opening a tenant database session.
    client = TestClient(app)

    try:
        response = client.request(
            method,
            request_path,
            **request_options,
        )
    finally:
        client.close()

    assert response.status_code == 418, response.text
    assert dependency_calls == [DEPENDENCY_MARKER]


def test_public_api_key_schema_excludes_credentials() -> None:
    fields = set(APIKeyPublic.model_fields)

    assert "id" in fields
    assert "workspace_id" in fields
    assert "secret" not in fields
    assert "secret_hash" not in fields