from __future__ import annotations

from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.modules.auth.models import (
    RefreshSession,
    User,
)


# =========================================================
# HELPERS
# =========================================================


async def get_user_by_email(
    db_session,
    email: str,
) -> User:
    result = await db_session.execute(
        select(User).where(
            User.email == email
        )
    )

    user = result.scalar_one_or_none()

    assert user is not None

    return user


async def get_user_sessions(
    db_session,
    user_id,
) -> list[RefreshSession]:
    result = await db_session.execute(
        select(RefreshSession)
        .where(
            RefreshSession.user_id == user_id
        )
        .order_by(
            RefreshSession.created_at.desc()
        )
    )

    return list(
        result.scalars().all()
    )


async def signup_and_verify(
    client: AsyncClient,
    payload: dict,
) -> None:
    signup_response = await client.post(
        "/api/v1/auth/signup",
        json=payload,
    )

    assert signup_response.status_code == 201, signup_response.text

    verify_response = await client.post(
        "/api/v1/auth/verify-email",
        json={
            "email": payload["email"],
            "otp": "123456",
        },
    )

    assert verify_response.status_code == 200, verify_response.text


def extract_user_from_me_response(
    data: dict,
) -> dict:
    """
    Support both common /me response shapes:

    {
        "email": "...",
        "username": "..."
    }

    or:

    {
        "user": {
            "email": "...",
            "username": "..."
        }
    }
    """

    user = data.get("user")

    if isinstance(user, dict):
        return user

    return data


# =========================================================
# LOGIN SUCCESS WITH EMAIL
# =========================================================


@pytest.mark.asyncio
async def test_login_success_with_email(
    client: AsyncClient,
    test_user_payload,
):
    await signup_and_verify(
        client,
        test_user_payload,
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "identifier": test_user_payload["email"],
            "password": test_user_payload["password"],
            "remember_me": False,
        },
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["access_token"]
    assert data["refresh_token"]

    assert data["token_type"].lower() == "bearer"

    assert data["user"]["email"] == test_user_payload["email"]
    assert data["user"]["username"] == test_user_payload["username"]

    assert data["user"]["is_email_verified"] is True
    assert data["user"]["is_active"] is True


# =========================================================
# LOGIN SUCCESS WITH USERNAME
# =========================================================


@pytest.mark.asyncio
async def test_login_success_with_username(
    client: AsyncClient,
    test_user_payload,
):
    await signup_and_verify(
        client,
        test_user_payload,
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "identifier": test_user_payload["username"],
            "password": test_user_payload["password"],
            "remember_me": False,
        },
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["access_token"]
    assert data["refresh_token"]

    assert data["user"]["username"] == test_user_payload["username"]


# =========================================================
# EMAIL IDENTIFIER NORMALIZATION
# =========================================================


@pytest.mark.asyncio
async def test_login_email_identifier_is_normalized(
    client: AsyncClient,
    test_user_payload,
):
    await signup_and_verify(
        client,
        test_user_payload,
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "identifier": "  TEST.AUTH@EXAMPLE.COM  ",
            "password": test_user_payload["password"],
            "remember_me": False,
        },
    )

    assert response.status_code == 200, response.text


# =========================================================
# USERNAME IDENTIFIER NORMALIZATION
# =========================================================


@pytest.mark.asyncio
async def test_login_username_identifier_is_normalized(
    client: AsyncClient,
    test_user_payload,
):
    await signup_and_verify(
        client,
        test_user_payload,
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "identifier": "  TestAuthUser  ",
            "password": test_user_payload["password"],
            "remember_me": False,
        },
    )

    assert response.status_code == 200, response.text


# =========================================================
# WRONG PASSWORD
# =========================================================


@pytest.mark.asyncio
async def test_login_wrong_password_rejected(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    await signup_and_verify(
        client,
        test_user_payload,
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "identifier": test_user_payload["email"],
            "password": "WrongPassword123!",
            "remember_me": False,
        },
    )

    assert response.status_code == 401, response.text

    data = response.json()

    assert "error" in data

    await db_session.rollback()

    user = await get_user_by_email(
        db_session,
        test_user_payload["email"],
    )

    assert user.is_email_verified is True


# =========================================================
# UNKNOWN USER
# =========================================================


@pytest.mark.asyncio
async def test_login_unknown_user_rejected(
    client: AsyncClient,
):
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "identifier": "missing.user@example.com",
            "password": "StrongPassword123!",
            "remember_me": False,
        },
    )

    assert response.status_code == 401, response.text


# =========================================================
# UNVERIFIED ACCOUNT
# =========================================================


@pytest.mark.asyncio
async def test_login_unverified_user_rejected(
    client: AsyncClient,
    test_user_payload,
):
    signup_response = await client.post(
        "/api/v1/auth/signup",
        json=test_user_payload,
    )

    assert signup_response.status_code == 201

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "identifier": test_user_payload["email"],
            "password": test_user_payload["password"],
            "remember_me": False,
        },
    )

    assert response.status_code == 401, response.text

    data = response.json()

    assert data["error"]["code"] == "EMAIL_NOT_VERIFIED"


# =========================================================
# INACTIVE ACCOUNT
# =========================================================


@pytest.mark.asyncio
async def test_login_inactive_user_rejected(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    await signup_and_verify(
        client,
        test_user_payload,
    )

    await db_session.rollback()

    user = await get_user_by_email(
        db_session,
        test_user_payload["email"],
    )

    user.is_active = False

    await db_session.commit()

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "identifier": test_user_payload["email"],
            "password": test_user_payload["password"],
            "remember_me": False,
        },
    )

    assert response.status_code == 401, response.text

    data = response.json()

    assert data["error"]["code"] == "ACCOUNT_DISABLED"


# =========================================================
# LOCKED ACCOUNT
# =========================================================


@pytest.mark.asyncio
async def test_login_locked_user_rejected(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    await signup_and_verify(
        client,
        test_user_payload,
    )

    await db_session.rollback()

    user = await get_user_by_email(
        db_session,
        test_user_payload["email"],
    )

    user.is_locked = True
    user.locked_at = datetime.now(timezone.utc)
    user.locked_reason = "Automated test lock."

    await db_session.commit()

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "identifier": test_user_payload["email"],
            "password": test_user_payload["password"],
            "remember_me": False,
        },
    )

    assert response.status_code == 401, response.text

    data = response.json()

    assert data["error"]["code"] == "ACCOUNT_LOCKED"


# =========================================================
# LAST LOGIN TIMESTAMP
# =========================================================


@pytest.mark.asyncio
async def test_successful_login_updates_last_login_at(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    await signup_and_verify(
        client,
        test_user_payload,
    )

    await db_session.rollback()

    before_login_user = await get_user_by_email(
        db_session,
        test_user_payload["email"],
    )

    assert before_login_user.last_login_at is None

    await db_session.rollback()

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "identifier": test_user_payload["email"],
            "password": test_user_payload["password"],
            "remember_me": False,
        },
    )

    assert response.status_code == 200, response.text

    await db_session.rollback()

    after_login_user = await get_user_by_email(
        db_session,
        test_user_payload["email"],
    )

    assert after_login_user.last_login_at is not None


# =========================================================
# SUCCESSFUL LOGIN CREATES REFRESH SESSION
# =========================================================


@pytest.mark.asyncio
async def test_login_creates_refresh_session(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    await signup_and_verify(
        client,
        test_user_payload,
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "identifier": test_user_payload["email"],
            "password": test_user_payload["password"],
            "remember_me": False,
        },
    )

    assert response.status_code == 200, response.text

    await db_session.rollback()

    user = await get_user_by_email(
        db_session,
        test_user_payload["email"],
    )

    user_id = user.id

    sessions = await get_user_sessions(
        db_session,
        user_id,
    )

    assert len(sessions) == 1

    session = sessions[0]

    assert session.user_id == user_id
    assert session.jti
    assert session.token_hash
    assert session.expires_at is not None
    assert session.revoked_at is None
    assert session.rotated_at is None


# =========================================================
# REFRESH TOKEN MUST NOT BE STORED PLAINTEXT
# =========================================================


@pytest.mark.asyncio
async def test_login_does_not_store_plaintext_refresh_token(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    await signup_and_verify(
        client,
        test_user_payload,
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "identifier": test_user_payload["email"],
            "password": test_user_payload["password"],
            "remember_me": False,
        },
    )

    assert response.status_code == 200, response.text

    data = response.json()

    refresh_token = data["refresh_token"]

    await db_session.rollback()

    user = await get_user_by_email(
        db_session,
        test_user_payload["email"],
    )

    user_id = user.id

    sessions = await get_user_sessions(
        db_session,
        user_id,
    )

    assert len(sessions) == 1

    session = sessions[0]

    assert session.token_hash
    assert session.token_hash != refresh_token
    assert refresh_token not in session.token_hash


# =========================================================
# ACCESS TOKEN AND REFRESH TOKEN DIFFER
# =========================================================


@pytest.mark.asyncio
async def test_access_and_refresh_tokens_are_different(
    client: AsyncClient,
    test_user_payload,
):
    await signup_and_verify(
        client,
        test_user_payload,
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "identifier": test_user_payload["email"],
            "password": test_user_payload["password"],
            "remember_me": False,
        },
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["access_token"]
    assert data["refresh_token"]

    assert data["access_token"] != data["refresh_token"]


# =========================================================
# ACCESS TOKEN CAN ACCESS /ME
# =========================================================


@pytest.mark.asyncio
async def test_login_access_token_can_access_me(
    client: AsyncClient,
    test_user_payload,
):
    await signup_and_verify(
        client,
        test_user_payload,
    )

    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "identifier": test_user_payload["email"],
            "password": test_user_payload["password"],
            "remember_me": False,
        },
    )

    assert login_response.status_code == 200, login_response.text

    login_data = login_response.json()

    access_token = login_data["access_token"]

    me_response = await client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert me_response.status_code == 200, me_response.text

    me_data = extract_user_from_me_response(
        me_response.json()
    )

    assert me_data["email"] == test_user_payload["email"]
    assert me_data["username"] == test_user_payload["username"]


# =========================================================
# INVALID ACCESS TOKEN
# =========================================================


@pytest.mark.asyncio
async def test_invalid_access_token_cannot_access_me(
    client: AsyncClient,
):
    response = await client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": "Bearer invalid.jwt.token",
        },
    )

    assert response.status_code in {
        401,
        403,
    }, response.text


# =========================================================
# MISSING ACCESS TOKEN
# =========================================================


@pytest.mark.asyncio
async def test_missing_access_token_cannot_access_me(
    client: AsyncClient,
):
    response = await client.get(
        "/api/v1/auth/me",
    )

    assert response.status_code in {
        401,
        403,
    }, response.text


# =========================================================
# PASSWORD HASH REMAINS SECURE
# =========================================================


@pytest.mark.asyncio
async def test_successful_login_does_not_replace_password_with_plaintext(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    await signup_and_verify(
        client,
        test_user_payload,
    )

    await db_session.rollback()

    user_before = await get_user_by_email(
        db_session,
        test_user_payload["email"],
    )

    password_hash_before = user_before.password_hash

    assert password_hash_before
    assert password_hash_before != test_user_payload["password"]

    await db_session.rollback()

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "identifier": test_user_payload["email"],
            "password": test_user_payload["password"],
            "remember_me": False,
        },
    )

    assert response.status_code == 200, response.text

    await db_session.rollback()

    user_after = await get_user_by_email(
        db_session,
        test_user_payload["email"],
    )

    assert user_after.password_hash
    assert user_after.password_hash != test_user_payload["password"]

    assert (
        test_user_payload["password"]
        not in user_after.password_hash
    )


# =========================================================
# WRONG PASSWORD MUST NOT CREATE SESSION
# =========================================================


@pytest.mark.asyncio
async def test_wrong_password_does_not_create_refresh_session(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    await signup_and_verify(
        client,
        test_user_payload,
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "identifier": test_user_payload["email"],
            "password": "WrongPassword123!",
            "remember_me": False,
        },
    )

    assert response.status_code == 401, response.text

    await db_session.rollback()

    user = await get_user_by_email(
        db_session,
        test_user_payload["email"],
    )

    user_id = user.id

    sessions = await get_user_sessions(
        db_session,
        user_id,
    )

    assert sessions == []


# =========================================================
# UNVERIFIED USER MUST NOT CREATE SESSION
# =========================================================


@pytest.mark.asyncio
async def test_unverified_user_does_not_create_refresh_session(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    signup_response = await client.post(
        "/api/v1/auth/signup",
        json=test_user_payload,
    )

    assert signup_response.status_code == 201

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "identifier": test_user_payload["email"],
            "password": test_user_payload["password"],
            "remember_me": False,
        },
    )

    assert response.status_code == 401, response.text

    data = response.json()

    assert data["error"]["code"] == "EMAIL_NOT_VERIFIED"

    await db_session.rollback()

    user = await get_user_by_email(
        db_session,
        test_user_payload["email"],
    )

    user_id = user.id

    sessions = await get_user_sessions(
        db_session,
        user_id,
    )

    assert sessions == []


# =========================================================
# MULTIPLE LOGINS CREATE MULTIPLE ACTIVE SESSIONS
# =========================================================


@pytest.mark.asyncio
async def test_multiple_logins_create_multiple_sessions(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    await signup_and_verify(
        client,
        test_user_payload,
    )

    first_response = await client.post(
        "/api/v1/auth/login",
        json={
            "identifier": test_user_payload["email"],
            "password": test_user_payload["password"],
            "remember_me": False,
        },
    )

    assert first_response.status_code == 200, first_response.text

    second_response = await client.post(
        "/api/v1/auth/login",
        json={
            "identifier": test_user_payload["email"],
            "password": test_user_payload["password"],
            "remember_me": False,
        },
    )

    assert second_response.status_code == 200, second_response.text

    await db_session.rollback()

    user = await get_user_by_email(
        db_session,
        test_user_payload["email"],
    )

    user_id = user.id

    sessions = await get_user_sessions(
        db_session,
        user_id,
    )

    assert len(sessions) == 2

    active_sessions = [
        session
        for session in sessions
        if session.revoked_at is None
    ]

    assert len(active_sessions) == 2


# =========================================================
# SESSION REQUEST METADATA
# =========================================================


@pytest.mark.asyncio
async def test_login_session_stores_request_metadata(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    await signup_and_verify(
        client,
        test_user_payload,
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "identifier": test_user_payload["email"],
            "password": test_user_payload["password"],
            "remember_me": False,
        },
        headers={
            "User-Agent": "WorkforceOS-Pytest/1.0",
        },
    )

    assert response.status_code == 200, response.text

    await db_session.rollback()

    user = await get_user_by_email(
        db_session,
        test_user_payload["email"],
    )

    user_id = user.id

    sessions = await get_user_sessions(
        db_session,
        user_id,
    )

    assert len(sessions) == 1

    session = sessions[0]

    assert session.user_agent is not None

    assert "WorkforceOS-Pytest" in session.user_agent


# =========================================================
# EMPTY IDENTIFIER
# =========================================================


@pytest.mark.asyncio
async def test_login_empty_identifier_rejected(
    client: AsyncClient,
):
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "identifier": "",
            "password": "StrongPassword123!",
            "remember_me": False,
        },
    )

    assert response.status_code == 422, response.text


# =========================================================
# EMPTY PASSWORD
# =========================================================


@pytest.mark.asyncio
async def test_login_empty_password_rejected(
    client: AsyncClient,
):
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "identifier": "test.auth@example.com",
            "password": "",
            "remember_me": False,
        },
    )

    assert response.status_code in {
        401,
        422,
    }, response.text