import importlib
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.modules.workspace_rbac.schemas import WorkspaceMemberRolesResponse


rbac_router = importlib.import_module("app.modules.workspace_rbac.router")

WORKSPACE_ID = uuid.uuid4()
MEMBERSHIP_ID = uuid.uuid4()
BASE = (
    f"/api/v1/workspaces/{WORKSPACE_ID}"
    f"/members/{MEMBERSHIP_ID}/roles"
)


def make_client():
    response = WorkspaceMemberRolesResponse(
        workspace_id=WORKSPACE_ID,
        membership_id=MEMBERSHIP_ID,
        primary_role_key="member",
        additional_role_keys=["reader"],
        effective_role_keys=["member", "reader"],
        permissions=["employees.read"],
    )

    service = SimpleNamespace(
        get_member_roles=AsyncMock(return_value=response),
        grant_member_role=AsyncMock(return_value=response),
        revoke_member_role=AsyncMock(return_value=response),
    )
    user = SimpleNamespace(id=uuid.uuid4())

    app = FastAPI()
    app.include_router(rbac_router.router, prefix="/api/v1")

    app.dependency_overrides[rbac_router.get_service] = lambda: service
    app.dependency_overrides[
        rbac_router.get_current_verified_user
    ] = lambda: user

    return TestClient(app), service, user, app


def test_list_roles_endpoint():
    client, service, user, _ = make_client()

    with client:
        response = client.get(BASE)

    assert response.status_code == 200
    assert response.json()["effective_role_keys"] == ["member", "reader"]

    service.get_member_roles.assert_awaited_once_with(
        workspace_id=WORKSPACE_ID,
        membership_id=MEMBERSHIP_ID,
        user=user,
    )


def test_grant_role_endpoint():
    client, service, user, _ = make_client()

    with client:
        response = client.put(BASE + "/reader")

    assert response.status_code == 200

    service.grant_member_role.assert_awaited_once_with(
        workspace_id=WORKSPACE_ID,
        membership_id=MEMBERSHIP_ID,
        role_key="reader",
        user=user,
    )


def test_revoke_role_endpoint():
    client, service, user, _ = make_client()

    with client:
        response = client.delete(BASE + "/reader")

    assert response.status_code == 200

    service.revoke_member_role.assert_awaited_once_with(
        workspace_id=WORKSPACE_ID,
        membership_id=MEMBERSHIP_ID,
        role_key="reader",
        user=user,
    )


def test_unverified_request_does_not_reach_service():
    client, service, _, app = make_client()

    def denied():
        raise HTTPException(
            status_code=403,
            detail="Verified user required.",
        )

    app.dependency_overrides[
        rbac_router.get_current_verified_user
    ] = denied

    with client:
        response = client.put(BASE + "/reader")

    assert response.status_code == 403
    service.grant_member_role.assert_not_awaited()


def test_invalid_membership_uuid_is_rejected():
    client, service, _, _ = make_client()

    with client:
        response = client.get(
            f"/api/v1/workspaces/{WORKSPACE_ID}"
            "/members/invalid/roles"
        )

    assert response.status_code == 422
    service.get_member_roles.assert_not_awaited()


def test_assignment_operations_registered_in_real_app_openapi():
    from app.main import app

    paths = app.openapi()["paths"]
    prefix = (
        "/api/v1/workspaces/{workspace_id}"
        "/members/{membership_id}/roles"
    )

    assert "get" in paths[prefix]
    assert "put" in paths[prefix + "/{role_key}"]
    assert "delete" in paths[prefix + "/{role_key}"]