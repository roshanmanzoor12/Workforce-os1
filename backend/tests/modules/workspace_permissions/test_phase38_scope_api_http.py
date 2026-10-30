from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.modules.workspace_rbac.scope_dependencies import (
    get_membership_scope_service,
)
from app.modules.workspace_rbac.scope_registration import (
    register_membership_scope_routes,
)


@pytest.fixture
def api():
    workspace_id = uuid.uuid4()
    membership_id = uuid.uuid4()
    resource_id = uuid.uuid4()
    grantor_id = uuid.uuid4()

    grant = {
        "membership_id": str(membership_id),
        "scope_type": "team",
        "resource_id": str(resource_id),
        "granted_by_user_id": str(grantor_id),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    service = SimpleNamespace(
        list_for=AsyncMock(
            return_value={
                "membership_id": str(membership_id),
                "grants": [grant],
            },
        ),
        grant=AsyncMock(return_value=grant),
        revoke=AsyncMock(
            return_value={
                "membership_id": str(membership_id),
                "scope_type": "team",
                "resource_id": str(resource_id),
                "removed": True,
            },
        ),
    )

    app = FastAPI()

    register_membership_scope_routes(
        app,
        prefix="/api/v1",
    )

    app.dependency_overrides[get_membership_scope_service] = (
        lambda: service
    )

    path = (
        f"/api/v1/workspaces/{workspace_id}"
        f"/members/{membership_id}/scopes"
    )

    with TestClient(app) as client:
        yield SimpleNamespace(
            app=app,
            client=client,
            service=service,
            path=path,
            membership_id=membership_id,
            resource_id=resource_id,
            grantor_id=grantor_id,
        )


def test_http_list_serializes_grants(api):
    response = api.client.get(api.path)

    assert response.status_code == 200
    assert response.json()["membership_id"] == str(api.membership_id)
    assert len(response.json()["grants"]) == 1

    api.service.list_for.assert_awaited_once_with(
        membership_id=api.membership_id,
    )


def test_http_grant_serializes_original_grantor(api):
    response = api.client.post(
        api.path,
        json={
            "scope_type": "team",
            "resource_id": str(api.resource_id),
        },
    )

    assert response.status_code == 200
    assert response.json()["granted_by_user_id"] == str(api.grantor_id)

    payload = api.service.grant.await_args.args[0]

    assert payload.scope_type == "team"
    assert payload.resource_id == api.resource_id
    assert (
        api.service.grant.await_args.kwargs["membership_id"]
        == api.membership_id
    )


def test_http_revoke_returns_removed_flag(api):
    response = api.client.delete(
        f"{api.path}/team/{api.resource_id}",
    )

    assert response.status_code == 200
    assert response.json()["removed"] is True

    api.service.revoke.assert_awaited_once_with(
        membership_id=api.membership_id,
        scope_type="team",
        resource_id=api.resource_id,
    )


def test_http_repeated_revoke_can_return_false(api):
    api.service.revoke.return_value["removed"] = False

    response = api.client.delete(
        f"{api.path}/team/{api.resource_id}",
    )

    assert response.status_code == 200
    assert response.json()["removed"] is False


@pytest.mark.parametrize(
    "scope_type",
    ["workspace", "self", "company", "shared", "TEAM", ""],
)
def test_http_rejects_unsupported_grant_scope(api, scope_type):
    response = api.client.post(
        api.path,
        json={
            "scope_type": scope_type,
            "resource_id": str(api.resource_id),
        },
    )

    assert response.status_code == 422
    api.service.grant.assert_not_awaited()


@pytest.mark.parametrize(
    "extra",
    [
        {"granted_by_user_id": str(uuid.uuid4())},
        {"workspace_id": str(uuid.uuid4())},
        {"permissions": ["employees.manage"]},
        {"role_key": "owner"},
    ],
)
def test_http_rejects_identity_or_permission_injection(api, extra):
    response = api.client.post(
        api.path,
        json={
            "scope_type": "team",
            "resource_id": str(api.resource_id),
            **extra,
        },
    )

    assert response.status_code == 422
    api.service.grant.assert_not_awaited()


def test_http_rejects_invalid_resource_uuid(api):
    response = api.client.post(
        api.path,
        json={
            "scope_type": "team",
            "resource_id": "not-a-uuid",
        },
    )

    assert response.status_code == 422
    api.service.grant.assert_not_awaited()


def test_http_rejects_invalid_membership_uuid(api):
    invalid_path = api.path.replace(
        str(api.membership_id),
        "not-a-uuid",
    )

    response = api.client.get(invalid_path)

    assert response.status_code == 422
    api.service.list_for.assert_not_awaited()


def test_http_rejects_workspace_scope_revocation(api):
    response = api.client.delete(
        f"{api.path}/workspace/{api.resource_id}",
    )

    assert response.status_code == 422
    api.service.revoke.assert_not_awaited()


@pytest.mark.parametrize("method", ["get", "post", "delete"])
def test_http_preserves_authorization_denial(api, method):
    async def denied():
        raise HTTPException(
            status_code=403,
            detail="Workspace access is denied.",
        )

    api.app.dependency_overrides[get_membership_scope_service] = denied

    if method == "post":
        response = api.client.post(
            api.path,
            json={
                "scope_type": "team",
                "resource_id": str(api.resource_id),
            },
        )
    elif method == "delete":
        response = api.client.delete(
            f"{api.path}/team/{api.resource_id}",
        )
    else:
        response = api.client.get(api.path)

    assert response.status_code == 403
    api.service.list_for.assert_not_awaited()
    api.service.grant.assert_not_awaited()
    api.service.revoke.assert_not_awaited()


def test_http_preserves_service_permission_denial(api):
    api.service.grant.side_effect = HTTPException(
        status_code=403,
        detail="Primary workspace owner required.",
    )

    response = api.client.post(
        api.path,
        json={
            "scope_type": "team",
            "resource_id": str(api.resource_id),
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Primary workspace owner required."
    )


def test_openapi_exposes_three_scope_operations(api):
    paths = api.app.openapi()["paths"]

    collection = (
        "/api/v1/workspaces/{workspace_id}"
        "/members/{membership_id}/scopes"
    )

    assert "get" in paths[collection]
    assert "post" in paths[collection]
    assert "delete" in paths[
        collection + "/{scope_type}/{resource_id}"
    ]

    schema = api.app.openapi()["components"]["schemas"][
        "ScopeGrantCreateRequest"
    ]

    assert schema["additionalProperties"] is False
    assert set(schema["properties"]) == {
        "scope_type",
        "resource_id",
    }