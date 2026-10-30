from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.modules.auth.models import User
from app.modules.workspaces.models import (
    MEMBERSHIP_STATUS_ACTIVE,
    MEMBERSHIP_STATUS_REMOVED,
    MEMBERSHIP_STATUS_SUSPENDED,
    TENANT_STATUS_DECOMMISSIONED,
    TENANT_STATUS_PENDING,
    TENANT_STATUS_SUSPENDED,
    WORKSPACE_ROLE_ADMIN,
    WORKSPACE_ROLE_MEMBER,
    WORKSPACE_ROLE_OWNER,
    WORKSPACE_STATUS_ARCHIVED,
    WORKSPACE_STATUS_PROVISIONING,
    WORKSPACE_STATUS_SUSPENDED,
    TenantDatabaseRegistry,
    Workspace,
    WorkspaceMembership,
)


# =========================================================
# CONSTANTS
# =========================================================

API_PREFIX = "/api/v1"

WORKSPACES_URL = f"{API_PREFIX}/workspaces"

TEST_OTP = "123456"


# =========================================================
# AUTH HELPERS
# =========================================================


def bearer_headers(
    access_token: str,
) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token}",
    }


async def signup_user(
    client: AsyncClient,
    payload: dict,
):
    return await client.post(
        f"{API_PREFIX}/auth/signup",
        json=payload,
    )


async def verify_email(
    client: AsyncClient,
    *,
    email: str,
):
    return await client.post(
        f"{API_PREFIX}/auth/verify-email",
        json={
            "email": email,
            "otp": TEST_OTP,
        },
    )


async def login_user(
    client: AsyncClient,
    *,
    identifier: str,
    password: str,
):
    return await client.post(
        f"{API_PREFIX}/auth/login",
        json={
            "identifier": identifier,
            "password": password,
            "remember_me": False,
        },
    )


async def create_verified_login(
    client: AsyncClient,
    payload: dict,
) -> dict:
    signup_response = await signup_user(
        client,
        payload,
    )

    assert signup_response.status_code == 201, (
        signup_response.text
    )

    verify_response = await verify_email(
        client,
        email=payload["email"],
    )

    assert verify_response.status_code == 200, (
        verify_response.text
    )

    login_response = await login_user(
        client,
        identifier=payload["email"],
        password=payload["password"],
    )

    assert login_response.status_code == 200, (
        login_response.text
    )

    data = login_response.json()

    assert data.get("access_token")

    return data


# =========================================================
# RESPONSE HELPERS
# =========================================================


def find_value(
    value,
    key: str,
):
    if isinstance(value, dict):
        if key in value:
            return value[key]

        for child in value.values():
            result = find_value(
                child,
                key,
            )

            if result is not None:
                return result

    elif isinstance(value, list):
        for child in value:
            result = find_value(
                child,
                key,
            )

            if result is not None:
                return result

    return None


def extract_workspace_id(
    body: dict,
) -> uuid.UUID:
    workspace = body.get(
        "workspace"
    )

    if isinstance(
        workspace,
        dict,
    ):
        workspace_id = workspace.get(
            "id"
        )

        if workspace_id:
            return uuid.UUID(
                str(workspace_id)
            )

    workspace_id = find_value(
        body,
        "id",
    )

    assert workspace_id is not None

    return uuid.UUID(
        str(workspace_id)
    )


# =========================================================
# DATABASE HELPERS
# =========================================================


async def get_user_by_email(
    db_session,
    email: str,
) -> User:
    statement = (
        select(User)
        .where(
            User.email == email
        )
        .execution_options(
            populate_existing=True
        )
    )

    result = await db_session.execute(
        statement
    )

    user = result.scalar_one_or_none()

    assert user is not None

    return user


async def get_workspace_by_id(
    db_session,
    workspace_id: uuid.UUID,
) -> Workspace:
    statement = (
        select(Workspace)
        .where(
            Workspace.id == workspace_id
        )
        .execution_options(
            populate_existing=True
        )
    )

    result = await db_session.execute(
        statement
    )

    workspace = result.scalar_one_or_none()

    assert workspace is not None

    return workspace


async def get_membership(
    db_session,
    *,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
) -> WorkspaceMembership:
    statement = (
        select(
            WorkspaceMembership
        )
        .where(
            WorkspaceMembership.workspace_id
            == workspace_id,
            WorkspaceMembership.user_id
            == user_id,
        )
        .execution_options(
            populate_existing=True
        )
    )

    result = await db_session.execute(
        statement
    )

    membership = result.scalar_one_or_none()

    assert membership is not None

    return membership


async def get_tenant_registry(
    db_session,
    workspace_id: uuid.UUID,
) -> TenantDatabaseRegistry:
    statement = (
        select(
            TenantDatabaseRegistry
        )
        .where(
            TenantDatabaseRegistry.workspace_id
            == workspace_id
        )
        .execution_options(
            populate_existing=True
        )
    )

    result = await db_session.execute(
        statement
    )

    tenant = result.scalar_one_or_none()

    assert tenant is not None

    return tenant


async def create_workspace_via_api(
    client: AsyncClient,
    *,
    access_token: str,
    name: str = "Acme Operations",
    slug: str | None = None,
):
    payload: dict[str, object] = {
        "name": name,
        "timezone": "UTC",
    }

    if slug is not None:
        payload["slug"] = slug

    response = await client.post(
        WORKSPACES_URL,
        headers=bearer_headers(
            access_token
        ),
        json=payload,
    )

    assert response.status_code == 201, (
        response.text
    )

    return response


async def add_membership(
    db_session,
    *,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    role_key: str = WORKSPACE_ROLE_MEMBER,
    status: str = MEMBERSHIP_STATUS_ACTIVE,
) -> WorkspaceMembership:
    membership = WorkspaceMembership(
        workspace_id=workspace_id,
        user_id=user_id,
        role_key=role_key,
        status=status,
    )

    db_session.add(
        membership
    )

    await db_session.commit()

    await db_session.refresh(
        membership
    )

    return membership


# =========================================================
# AUTHENTICATION
# =========================================================


@pytest.mark.asyncio
async def test_create_workspace_requires_authentication(
    client: AsyncClient,
):
    response = await client.post(
        WORKSPACES_URL,
        json={
            "name": "Unauthenticated Workspace",
            "timezone": "UTC",
        },
    )

    assert response.status_code == 401, (
        response.text
    )


@pytest.mark.asyncio
async def test_list_workspaces_requires_authentication(
    client: AsyncClient,
):
    response = await client.get(
        WORKSPACES_URL
    )

    assert response.status_code == 401, (
        response.text
    )


# =========================================================
# WORKSPACE CREATION
# =========================================================


@pytest.mark.asyncio
async def test_create_workspace_success(
    client: AsyncClient,
    test_user_payload,
):
    login_data = await create_verified_login(
        client,
        test_user_payload,
    )

    response = await create_workspace_via_api(
        client,
        access_token=login_data[
            "access_token"
        ],
    )

    workspace_id = extract_workspace_id(
        response.json()
    )

    assert isinstance(
        workspace_id,
        uuid.UUID,
    )


@pytest.mark.asyncio
async def test_create_workspace_persists_control_records(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    login_data = await create_verified_login(
        client,
        test_user_payload,
    )

    response = await create_workspace_via_api(
        client,
        access_token=login_data[
            "access_token"
        ],
        name="Control Plane Test",
    )

    workspace_id = extract_workspace_id(
        response.json()
    )

    user = await get_user_by_email(
        db_session,
        test_user_payload["email"],
    )

    workspace = await get_workspace_by_id(
        db_session,
        workspace_id,
    )

    membership = await get_membership(
        db_session,
        workspace_id=workspace_id,
        user_id=user.id,
    )

    tenant = await get_tenant_registry(
        db_session,
        workspace_id,
    )

    assert workspace.name == (
        "Control Plane Test"
    )

    assert workspace.status == (
        WORKSPACE_STATUS_PROVISIONING
    )

    assert workspace.is_active is True

    assert membership.role_key == (
        WORKSPACE_ROLE_OWNER
    )

    assert membership.status == (
        MEMBERSHIP_STATUS_ACTIVE
    )

    assert tenant.status == (
        TENANT_STATUS_PENDING
    )


@pytest.mark.asyncio
async def test_workspace_creator_becomes_owner(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    login_data = await create_verified_login(
        client,
        test_user_payload,
    )

    response = await create_workspace_via_api(
        client,
        access_token=login_data[
            "access_token"
        ],
    )

    workspace_id = extract_workspace_id(
        response.json()
    )

    user = await get_user_by_email(
        db_session,
        test_user_payload["email"],
    )

    membership = await get_membership(
        db_session,
        workspace_id=workspace_id,
        user_id=user.id,
    )

    assert membership.role_key == (
        WORKSPACE_ROLE_OWNER
    )

    assert membership.status == (
        MEMBERSHIP_STATUS_ACTIVE
    )


@pytest.mark.asyncio
async def test_tenant_database_name_is_server_generated(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    login_data = await create_verified_login(
        client,
        test_user_payload,
    )

    response = await create_workspace_via_api(
        client,
        access_token=login_data[
            "access_token"
        ],
    )

    workspace_id = extract_workspace_id(
        response.json()
    )

    tenant = await get_tenant_registry(
        db_session,
        workspace_id,
    )

    assert tenant.database_name

    assert tenant.database_name == (
        f"tenant_{workspace_id.hex}"
    )

    assert tenant.database_name.startswith(
        "tenant_"
    )


@pytest.mark.asyncio
async def test_client_cannot_choose_tenant_database_name(
    client: AsyncClient,
    test_user_payload,
):
    login_data = await create_verified_login(
        client,
        test_user_payload,
    )

    response = await client.post(
        WORKSPACES_URL,
        headers=bearer_headers(
            login_data["access_token"]
        ),
        json={
            "name": "Malicious Tenant Selection",
            "timezone": "UTC",
            "database_name": "postgres",
        },
    )

    assert response.status_code == 422, (
        response.text
    )


@pytest.mark.asyncio
async def test_workspace_slug_is_server_allocated_when_omitted(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    login_data = await create_verified_login(
        client,
        test_user_payload,
    )

    response = await create_workspace_via_api(
        client,
        access_token=login_data[
            "access_token"
        ],
        name="Example Engineering Team",
    )

    workspace_id = extract_workspace_id(
        response.json()
    )

    workspace = await get_workspace_by_id(
        db_session,
        workspace_id,
    )

    assert workspace.slug

    assert workspace.slug.startswith(
        "example-engineering-team"
    )


@pytest.mark.asyncio
async def test_duplicate_requested_slug_is_rejected(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    login_data = await create_verified_login(
        client,
        test_user_payload,
    )

    first_response = await create_workspace_via_api(
        client,
        access_token=login_data[
            "access_token"
        ],
        name="First Workspace",
        slug="shared-slug",
    )

    first_id = extract_workspace_id(
        first_response.json()
    )

    second_response = await client.post(
        WORKSPACES_URL,
        headers=bearer_headers(
            login_data[
                "access_token"
            ]
        ),
        json={
            "name": "Second Workspace",
            "timezone": "UTC",
            "slug": "shared-slug",
        },
    )

    assert second_response.status_code == 409, (
        second_response.text
    )

    data = second_response.json()

    assert data["error"]["code"] == (
        "CONFLICT"
    )

    first_workspace = await get_workspace_by_id(
        db_session,
        first_id,
    )

    assert first_workspace.slug == (
        "shared-slug"
    )


# =========================================================
# LIST / GET
# =========================================================


@pytest.mark.asyncio
async def test_user_can_list_own_workspaces(
    client: AsyncClient,
    test_user_payload,
):
    login_data = await create_verified_login(
        client,
        test_user_payload,
    )

    create_response = await create_workspace_via_api(
        client,
        access_token=login_data[
            "access_token"
        ],
        name="Listed Workspace",
    )

    workspace_id = extract_workspace_id(
        create_response.json()
    )

    response = await client.get(
        WORKSPACES_URL,
        headers=bearer_headers(
            login_data["access_token"]
        ),
    )

    assert response.status_code == 200, (
        response.text
    )

    assert str(workspace_id) in (
        response.text
    )


@pytest.mark.asyncio
async def test_user_can_get_own_workspace(
    client: AsyncClient,
    test_user_payload,
):
    login_data = await create_verified_login(
        client,
        test_user_payload,
    )

    create_response = await create_workspace_via_api(
        client,
        access_token=login_data[
            "access_token"
        ],
    )

    workspace_id = extract_workspace_id(
        create_response.json()
    )

    response = await client.get(
        f"{WORKSPACES_URL}/{workspace_id}",
        headers=bearer_headers(
            login_data["access_token"]
        ),
    )

    assert response.status_code == 200, (
        response.text
    )

    assert str(workspace_id) in (
        response.text
    )


@pytest.mark.asyncio
async def test_user_cannot_get_another_users_workspace(
    client: AsyncClient,
    test_user_payload,
    second_test_user_payload,
):
    first_login = await create_verified_login(
        client,
        test_user_payload,
    )

    create_response = await create_workspace_via_api(
        client,
        access_token=first_login[
            "access_token"
        ],
    )

    workspace_id = extract_workspace_id(
        create_response.json()
    )

    second_login = await create_verified_login(
        client,
        second_test_user_payload,
    )

    response = await client.get(
        f"{WORKSPACES_URL}/{workspace_id}",
        headers=bearer_headers(
            second_login["access_token"]
        ),
    )

    assert response.status_code in {
        400,
        403,
        404,
    }, response.text


@pytest.mark.asyncio
async def test_workspace_list_does_not_leak_another_users_workspace(
    client: AsyncClient,
    test_user_payload,
    second_test_user_payload,
):
    first_login = await create_verified_login(
        client,
        test_user_payload,
    )

    create_response = await create_workspace_via_api(
        client,
        access_token=first_login[
            "access_token"
        ],
        name="Private Workspace",
    )

    workspace_id = extract_workspace_id(
        create_response.json()
    )

    second_login = await create_verified_login(
        client,
        second_test_user_payload,
    )

    response = await client.get(
        WORKSPACES_URL,
        headers=bearer_headers(
            second_login["access_token"]
        ),
    )

    assert response.status_code == 200, (
        response.text
    )

    assert str(workspace_id) not in (
        response.text
    )


# =========================================================
# WORKSPACE UPDATE
# =========================================================


@pytest.mark.asyncio
async def test_owner_can_update_workspace(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    login_data = await create_verified_login(
        client,
        test_user_payload,
    )

    create_response = await create_workspace_via_api(
        client,
        access_token=login_data[
            "access_token"
        ],
    )

    workspace_id = extract_workspace_id(
        create_response.json()
    )

    response = await client.patch(
        f"{WORKSPACES_URL}/{workspace_id}",
        headers=bearer_headers(
            login_data["access_token"]
        ),
        json={
            "name": "Updated Workspace Name",
            "timezone": "Asia/Karachi",
        },
    )

    assert response.status_code == 200, (
        response.text
    )

    workspace = await get_workspace_by_id(
        db_session,
        workspace_id,
    )

    assert workspace.name == (
        "Updated Workspace Name"
    )

    assert workspace.timezone == (
        "Asia/Karachi"
    )


@pytest.mark.asyncio
async def test_member_cannot_update_workspace(
    client: AsyncClient,
    db_session,
    test_user_payload,
    second_test_user_payload,
):
    owner_login = await create_verified_login(
        client,
        test_user_payload,
    )

    create_response = await create_workspace_via_api(
        client,
        access_token=owner_login[
            "access_token"
        ],
    )

    workspace_id = extract_workspace_id(
        create_response.json()
    )

    member_login = await create_verified_login(
        client,
        second_test_user_payload,
    )

    member_user = await get_user_by_email(
        db_session,
        second_test_user_payload["email"],
    )

    await add_membership(
        db_session,
        workspace_id=workspace_id,
        user_id=member_user.id,
        role_key=WORKSPACE_ROLE_MEMBER,
    )

    response = await client.patch(
        f"{WORKSPACES_URL}/{workspace_id}",
        headers=bearer_headers(
            member_login["access_token"]
        ),
        json={
            "name": "Unauthorized Rename",
        },
    )

    assert response.status_code == 422, (
        response.text
    )

    data = response.json()

    assert data["error"]["code"] == (
        "VALIDATION_ERROR"
    )

    workspace = await get_workspace_by_id(
        db_session,
        workspace_id,
    )

    assert workspace.name != (
        "Unauthorized Rename"
    )


# =========================================================
# MEMBERSHIP ROLE MANAGEMENT
# =========================================================


@pytest.mark.asyncio
async def test_owner_can_promote_member_to_admin(
    client: AsyncClient,
    db_session,
    test_user_payload,
    second_test_user_payload,
):
    owner_login = await create_verified_login(
        client,
        test_user_payload,
    )

    create_response = await create_workspace_via_api(
        client,
        access_token=owner_login[
            "access_token"
        ],
    )

    workspace_id = extract_workspace_id(
        create_response.json()
    )

    await create_verified_login(
        client,
        second_test_user_payload,
    )

    second_user = await get_user_by_email(
        db_session,
        second_test_user_payload["email"],
    )

    membership = await add_membership(
        db_session,
        workspace_id=workspace_id,
        user_id=second_user.id,
        role_key=WORKSPACE_ROLE_MEMBER,
    )

    membership_id = membership.id

    response = await client.patch(
        (
            f"{WORKSPACES_URL}/{workspace_id}"
            f"/memberships/{membership_id}/role"
        ),
        headers=bearer_headers(
            owner_login["access_token"]
        ),
        json={
            "role_key": WORKSPACE_ROLE_ADMIN,
        },
    )

    assert response.status_code == 200, (
        response.text
    )

    refreshed = await get_membership(
        db_session,
        workspace_id=workspace_id,
        user_id=second_user.id,
    )

    assert refreshed.role_key == (
        WORKSPACE_ROLE_ADMIN
    )


@pytest.mark.asyncio
async def test_last_owner_cannot_demote_self(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    owner_login = await create_verified_login(
        client,
        test_user_payload,
    )

    create_response = await create_workspace_via_api(
        client,
        access_token=owner_login[
            "access_token"
        ],
    )

    workspace_id = extract_workspace_id(
        create_response.json()
    )

    owner_user = await get_user_by_email(
        db_session,
        test_user_payload["email"],
    )

    owner_membership = await get_membership(
        db_session,
        workspace_id=workspace_id,
        user_id=owner_user.id,
    )

    membership_id = (
        owner_membership.id
    )

    response = await client.patch(
        (
            f"{WORKSPACES_URL}/{workspace_id}"
            f"/memberships/{membership_id}/role"
        ),
        headers=bearer_headers(
            owner_login["access_token"]
        ),
        json={
            "role_key": WORKSPACE_ROLE_ADMIN,
        },
    )

    assert response.status_code in {
        400,
        409,
        422,
    }, response.text

    refreshed = await get_membership(
        db_session,
        workspace_id=workspace_id,
        user_id=owner_user.id,
    )

    assert refreshed.role_key == (
        WORKSPACE_ROLE_OWNER
    )


# =========================================================
# MEMBERSHIP STATUS
# =========================================================


@pytest.mark.asyncio
async def test_owner_can_suspend_member(
    client: AsyncClient,
    db_session,
    test_user_payload,
    second_test_user_payload,
):
    owner_login = await create_verified_login(
        client,
        test_user_payload,
    )

    create_response = await create_workspace_via_api(
        client,
        access_token=owner_login[
            "access_token"
        ],
    )

    workspace_id = extract_workspace_id(
        create_response.json()
    )

    await create_verified_login(
        client,
        second_test_user_payload,
    )

    member_user = await get_user_by_email(
        db_session,
        second_test_user_payload["email"],
    )

    member = await add_membership(
        db_session,
        workspace_id=workspace_id,
        user_id=member_user.id,
    )

    membership_id = member.id

    response = await client.patch(
        (
            f"{WORKSPACES_URL}/{workspace_id}"
            f"/memberships/{membership_id}/status"
        ),
        headers=bearer_headers(
            owner_login["access_token"]
        ),
        json={
            "status": (
                MEMBERSHIP_STATUS_SUSPENDED
            ),
        },
    )

    assert response.status_code == 200, (
        response.text
    )

    refreshed = await get_membership(
        db_session,
        workspace_id=workspace_id,
        user_id=member_user.id,
    )

    assert refreshed.status == (
        MEMBERSHIP_STATUS_SUSPENDED
    )


@pytest.mark.asyncio
async def test_suspended_membership_loses_workspace_access(
    client: AsyncClient,
    db_session,
    test_user_payload,
    second_test_user_payload,
):
    owner_login = await create_verified_login(
        client,
        test_user_payload,
    )

    create_response = await create_workspace_via_api(
        client,
        access_token=owner_login[
            "access_token"
        ],
    )

    workspace_id = extract_workspace_id(
        create_response.json()
    )

    member_login = await create_verified_login(
        client,
        second_test_user_payload,
    )

    member_user = await get_user_by_email(
        db_session,
        second_test_user_payload["email"],
    )

    member = await add_membership(
        db_session,
        workspace_id=workspace_id,
        user_id=member_user.id,
    )

    membership_id = member.id

    suspend_response = await client.patch(
        (
            f"{WORKSPACES_URL}/{workspace_id}"
            f"/memberships/{membership_id}/status"
        ),
        headers=bearer_headers(
            owner_login["access_token"]
        ),
        json={
            "status": (
                MEMBERSHIP_STATUS_SUSPENDED
            ),
        },
    )

    assert suspend_response.status_code == 200, (
        suspend_response.text
    )

    response = await client.get(
        f"{WORKSPACES_URL}/{workspace_id}",
        headers=bearer_headers(
            member_login["access_token"]
        ),
    )

    assert response.status_code in {
        400,
        403,
        404,
    }, response.text


# =========================================================
# MEMBERSHIP REMOVAL
# =========================================================


@pytest.mark.asyncio
async def test_owner_can_remove_member(
    client: AsyncClient,
    db_session,
    test_user_payload,
    second_test_user_payload,
):
    owner_login = await create_verified_login(
        client,
        test_user_payload,
    )

    create_response = await create_workspace_via_api(
        client,
        access_token=owner_login[
            "access_token"
        ],
    )

    workspace_id = extract_workspace_id(
        create_response.json()
    )

    await create_verified_login(
        client,
        second_test_user_payload,
    )

    member_user = await get_user_by_email(
        db_session,
        second_test_user_payload["email"],
    )

    member = await add_membership(
        db_session,
        workspace_id=workspace_id,
        user_id=member_user.id,
    )

    membership_id = member.id

    response = await client.delete(
        (
            f"{WORKSPACES_URL}/{workspace_id}"
            f"/memberships/{membership_id}"
        ),
        headers=bearer_headers(
            owner_login["access_token"]
        ),
    )

    assert response.status_code == 200, (
        response.text
    )

    refreshed = await get_membership(
        db_session,
        workspace_id=workspace_id,
        user_id=member_user.id,
    )

    assert refreshed.status == (
        MEMBERSHIP_STATUS_REMOVED
    )


@pytest.mark.asyncio
async def test_last_owner_cannot_remove_self(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    owner_login = await create_verified_login(
        client,
        test_user_payload,
    )

    create_response = await create_workspace_via_api(
        client,
        access_token=owner_login[
            "access_token"
        ],
    )

    workspace_id = extract_workspace_id(
        create_response.json()
    )

    owner = await get_user_by_email(
        db_session,
        test_user_payload["email"],
    )

    membership = await get_membership(
        db_session,
        workspace_id=workspace_id,
        user_id=owner.id,
    )

    membership_id = membership.id

    response = await client.delete(
        (
            f"{WORKSPACES_URL}/{workspace_id}"
            f"/memberships/{membership_id}"
        ),
        headers=bearer_headers(
            owner_login["access_token"]
        ),
    )

    assert response.status_code in {
        400,
        409,
        422,
    }, response.text

    refreshed = await get_membership(
        db_session,
        workspace_id=workspace_id,
        user_id=owner.id,
    )

    assert refreshed.role_key == (
        WORKSPACE_ROLE_OWNER
    )

    assert refreshed.status == (
        MEMBERSHIP_STATUS_ACTIVE
    )


# =========================================================
# SUSPEND WORKSPACE
# =========================================================


@pytest.mark.asyncio
async def test_owner_can_suspend_workspace(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    owner_login = await create_verified_login(
        client,
        test_user_payload,
    )

    create_response = await create_workspace_via_api(
        client,
        access_token=owner_login[
            "access_token"
        ],
    )

    workspace_id = extract_workspace_id(
        create_response.json()
    )

    response = await client.post(
        f"{WORKSPACES_URL}/{workspace_id}/suspend",
        headers=bearer_headers(
            owner_login["access_token"]
        ),
    )

    assert response.status_code == 200, (
        response.text
    )

    workspace = await get_workspace_by_id(
        db_session,
        workspace_id,
    )

    tenant = await get_tenant_registry(
        db_session,
        workspace_id,
    )

    assert workspace.status == (
        WORKSPACE_STATUS_SUSPENDED
    )

    assert tenant.status == (
        TENANT_STATUS_SUSPENDED
    )


# =========================================================
# ARCHIVE WORKSPACE
# =========================================================


@pytest.mark.asyncio
async def test_owner_can_archive_workspace(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    owner_login = await create_verified_login(
        client,
        test_user_payload,
    )

    create_response = await create_workspace_via_api(
        client,
        access_token=owner_login[
            "access_token"
        ],
    )

    workspace_id = extract_workspace_id(
        create_response.json()
    )

    response = await client.post(
        f"{WORKSPACES_URL}/{workspace_id}/archive",
        headers=bearer_headers(
            owner_login["access_token"]
        ),
    )

    assert response.status_code == 200, (
        response.text
    )

    workspace = await get_workspace_by_id(
        db_session,
        workspace_id,
    )

    tenant = await get_tenant_registry(
        db_session,
        workspace_id,
    )

    assert workspace.status == (
        WORKSPACE_STATUS_ARCHIVED
    )

    assert workspace.is_active is False

    assert tenant.status == (
        TENANT_STATUS_DECOMMISSIONED
    )


# =========================================================
# RESPONSE SECURITY
# =========================================================


@pytest.mark.asyncio
async def test_workspace_api_does_not_expose_database_name(
    client: AsyncClient,
    test_user_payload,
):
    login_data = await create_verified_login(
        client,
        test_user_payload,
    )

    create_response = await create_workspace_via_api(
        client,
        access_token=login_data[
            "access_token"
        ],
    )

    workspace_id = extract_workspace_id(
        create_response.json()
    )

    create_body = (
        create_response.text.lower()
    )

    assert "database_name" not in create_body

    detail_response = await client.get(
        f"{WORKSPACES_URL}/{workspace_id}",
        headers=bearer_headers(
            login_data["access_token"]
        ),
    )

    assert detail_response.status_code == 200, (
        detail_response.text
    )

    detail_body = (
        detail_response.text.lower()
    )

    assert "database_name" not in detail_body
    assert "database_url" not in detail_body
    assert "postgresql://" not in detail_body
    assert "asyncpg" not in detail_body