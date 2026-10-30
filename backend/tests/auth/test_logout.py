from __future__ import annotations

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


async def login_user(
    client: AsyncClient,
    payload: dict,
    *,
    user_agent: str | None = None,
) -> dict:
    headers: dict[str, str] = {}

    if user_agent:
        headers["User-Agent"] = user_agent

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "identifier": payload["email"],
            "password": payload["password"],
            "remember_me": False,
        },
        headers=headers,
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["access_token"]
    assert data["refresh_token"]

    return data


async def create_logged_in_user(
    client: AsyncClient,
    payload: dict,
    *,
    user_agent: str | None = None,
) -> dict:
    await signup_and_verify(
        client,
        payload,
    )

    return await login_user(
        client,
        payload,
        user_agent=user_agent,
    )


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
            RefreshSession.created_at.asc()
        )
    )

    return list(
        result.scalars().all()
    )


async def get_session_by_id(
    db_session,
    session_id,
) -> RefreshSession | None:
    result = await db_session.execute(
        select(RefreshSession).where(
            RefreshSession.id == session_id
        )
    )

    return result.scalar_one_or_none()


def bearer_headers(
    access_token: str,
) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token}"
    }


# =========================================================
# LOGOUT REQUIRES REFRESH TOKEN
# =========================================================


@pytest.mark.asyncio
async def test_logout_missing_refresh_token_rejected(
    client: AsyncClient,
):
    response = await client.post(
        "/api/v1/auth/logout",
        json={},
    )

    assert response.status_code == 422, response.text


# =========================================================
# INVALID REFRESH TOKEN
# =========================================================


@pytest.mark.asyncio
async def test_logout_invalid_refresh_token_rejected(
    client: AsyncClient,
):
    response = await client.post(
        "/api/v1/auth/logout",
        json={
            "refresh_token": "invalid.refresh.token",
        },
    )

    assert response.status_code in {
        400,
        401,
        403,
        422,
    }, response.text


# =========================================================
# EMPTY REFRESH TOKEN
# =========================================================


@pytest.mark.asyncio
async def test_logout_empty_refresh_token_rejected(
    client: AsyncClient,
):
    response = await client.post(
        "/api/v1/auth/logout",
        json={
            "refresh_token": "",
        },
    )

    assert response.status_code in {
        400,
        401,
        403,
        422,
    }, response.text


# =========================================================
# VALID LOGOUT
# =========================================================


@pytest.mark.asyncio
async def test_logout_valid_refresh_token_succeeds(
    client: AsyncClient,
    test_user_payload,
):
    data = await create_logged_in_user(
        client,
        test_user_payload,
    )

    response = await client.post(
        "/api/v1/auth/logout",
        json={
            "refresh_token": data["refresh_token"],
        },
    )

    assert response.status_code in {
        200,
        204,
    }, response.text


# =========================================================
# LOGOUT REVOKES SESSION
# =========================================================


@pytest.mark.asyncio
async def test_logout_revokes_refresh_session(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    data = await create_logged_in_user(
        client,
        test_user_payload,
    )

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

    session_id = sessions[0].id

    await db_session.rollback()

    response = await client.post(
        "/api/v1/auth/logout",
        json={
            "refresh_token": data["refresh_token"],
        },
    )

    assert response.status_code in {
        200,
        204,
    }, response.text

    await db_session.rollback()

    session = await get_session_by_id(
        db_session,
        session_id,
    )

    assert session is not None
    assert session.revoked_at is not None


# =========================================================
# LOGOUT PRESERVES SESSION RECORD
# =========================================================


@pytest.mark.asyncio
async def test_logout_does_not_delete_session_record(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    data = await create_logged_in_user(
        client,
        test_user_payload,
    )

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

    session_id = sessions[0].id

    await db_session.rollback()

    response = await client.post(
        "/api/v1/auth/logout",
        json={
            "refresh_token": data["refresh_token"],
        },
    )

    assert response.status_code in {
        200,
        204,
    }, response.text

    await db_session.rollback()

    session = await get_session_by_id(
        db_session,
        session_id,
    )

    assert session is not None
    assert session.id == session_id
    assert session.revoked_at is not None


# =========================================================
# LOGGED OUT REFRESH TOKEN CANNOT REFRESH
# =========================================================


@pytest.mark.asyncio
async def test_logged_out_refresh_token_cannot_be_reused(
    client: AsyncClient,
    test_user_payload,
):
    data = await create_logged_in_user(
        client,
        test_user_payload,
    )

    refresh_token = data["refresh_token"]

    logout_response = await client.post(
        "/api/v1/auth/logout",
        json={
            "refresh_token": refresh_token,
        },
    )

    assert logout_response.status_code in {
        200,
        204,
    }, logout_response.text

    refresh_response = await client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": refresh_token,
        },
    )

    assert refresh_response.status_code in {
        400,
        401,
        403,
        409,
    }, refresh_response.text


# =========================================================
# LOGOUT ONE SESSION ONLY
# =========================================================


@pytest.mark.asyncio
async def test_logout_one_session_does_not_revoke_other_session(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    await signup_and_verify(
        client,
        test_user_payload,
    )

    first_login = await login_user(
        client,
        test_user_payload,
        user_agent="WorkforceOS-Desktop",
    )

    second_login = await login_user(
        client,
        test_user_payload,
        user_agent="WorkforceOS-Mobile",
    )

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

    first_session_id = sessions[0].id
    second_session_id = sessions[1].id

    await db_session.rollback()

    response = await client.post(
        "/api/v1/auth/logout",
        json={
            "refresh_token": first_login["refresh_token"],
        },
    )

    assert response.status_code in {
        200,
        204,
    }, response.text

    await db_session.rollback()

    first_session = await get_session_by_id(
        db_session,
        first_session_id,
    )

    second_session = await get_session_by_id(
        db_session,
        second_session_id,
    )

    assert first_session is not None
    assert second_session is not None

    assert first_session.revoked_at is not None
    assert second_session.revoked_at is None

    second_refresh = await client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": second_login["refresh_token"],
        },
    )

    assert second_refresh.status_code == 200, second_refresh.text


# =========================================================
# LOGOUT DOES NOT DISABLE USER
# =========================================================


@pytest.mark.asyncio
async def test_logout_does_not_disable_account(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    data = await create_logged_in_user(
        client,
        test_user_payload,
    )

    response = await client.post(
        "/api/v1/auth/logout",
        json={
            "refresh_token": data["refresh_token"],
        },
    )

    assert response.status_code in {
        200,
        204,
    }, response.text

    await db_session.rollback()

    user = await get_user_by_email(
        db_session,
        test_user_payload["email"],
    )

    assert user.is_active is True
    assert user.is_locked is False
    assert user.is_email_verified is True


# =========================================================
# USER CAN LOGIN AGAIN AFTER LOGOUT
# =========================================================


@pytest.mark.asyncio
async def test_user_can_login_again_after_logout(
    client: AsyncClient,
    test_user_payload,
):
    data = await create_logged_in_user(
        client,
        test_user_payload,
    )

    logout_response = await client.post(
        "/api/v1/auth/logout",
        json={
            "refresh_token": data["refresh_token"],
        },
    )

    assert logout_response.status_code in {
        200,
        204,
    }, logout_response.text

    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "identifier": test_user_payload["email"],
            "password": test_user_payload["password"],
            "remember_me": False,
        },
    )

    assert login_response.status_code == 200, login_response.text

    new_data = login_response.json()

    assert new_data["access_token"]
    assert new_data["refresh_token"]

    assert (
        new_data["refresh_token"]
        != data["refresh_token"]
    )


# =========================================================
# LOGOUT-ALL REQUIRES AUTH
# =========================================================


@pytest.mark.asyncio
async def test_logout_all_requires_authentication(
    client: AsyncClient,
):
    response = await client.post(
        "/api/v1/auth/logout-all",
    )

    assert response.status_code in {
        401,
        403,
    }, response.text


# =========================================================
# LOGOUT-ALL INVALID ACCESS TOKEN
# =========================================================


@pytest.mark.asyncio
async def test_logout_all_invalid_access_token_rejected(
    client: AsyncClient,
):
    response = await client.post(
        "/api/v1/auth/logout-all",
        headers={
            "Authorization": "Bearer invalid.jwt.token",
        },
    )

    assert response.status_code in {
        401,
        403,
    }, response.text


# =========================================================
# LOGOUT-ALL SUCCESS
# =========================================================


@pytest.mark.asyncio
async def test_logout_all_succeeds(
    client: AsyncClient,
    test_user_payload,
):
    data = await create_logged_in_user(
        client,
        test_user_payload,
    )

    response = await client.post(
        "/api/v1/auth/logout-all",
        headers=bearer_headers(
            data["access_token"]
        ),
    )

    assert response.status_code in {
        200,
        204,
    }, response.text


# =========================================================
# LOGOUT-ALL REVOKES ALL SESSIONS
# =========================================================


@pytest.mark.asyncio
async def test_logout_all_revokes_all_user_sessions(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    await signup_and_verify(
        client,
        test_user_payload,
    )

    first = await login_user(
        client,
        test_user_payload,
        user_agent="Device-One",
    )

    second = await login_user(
        client,
        test_user_payload,
        user_agent="Device-Two",
    )

    third = await login_user(
        client,
        test_user_payload,
        user_agent="Device-Three",
    )

    assert first["refresh_token"]
    assert second["refresh_token"]
    assert third["refresh_token"]

    response = await client.post(
        "/api/v1/auth/logout-all",
        headers=bearer_headers(
            third["access_token"]
        ),
    )

    assert response.status_code in {
        200,
        204,
    }, response.text

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

    assert len(sessions) == 3

    assert all(
        session.revoked_at is not None
        for session in sessions
    )


# =========================================================
# LOGOUT-ALL PRESERVES SESSION HISTORY
# =========================================================


@pytest.mark.asyncio
async def test_logout_all_preserves_session_records(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    await signup_and_verify(
        client,
        test_user_payload,
    )

    first = await login_user(
        client,
        test_user_payload,
    )

    second = await login_user(
        client,
        test_user_payload,
    )

    response = await client.post(
        "/api/v1/auth/logout-all",
        headers=bearer_headers(
            second["access_token"]
        ),
    )

    assert response.status_code in {
        200,
        204,
    }, response.text

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

    assert all(
        session.revoked_at is not None
        for session in sessions
    )

    assert first["refresh_token"]
    assert second["refresh_token"]


# =========================================================
# LOGOUT-ALL INVALIDATES ALL REFRESH TOKENS
# =========================================================


@pytest.mark.asyncio
async def test_logout_all_invalidates_all_refresh_tokens(
    client: AsyncClient,
    test_user_payload,
):
    await signup_and_verify(
        client,
        test_user_payload,
    )

    first = await login_user(
        client,
        test_user_payload,
    )

    second = await login_user(
        client,
        test_user_payload,
    )

    logout_response = await client.post(
        "/api/v1/auth/logout-all",
        headers=bearer_headers(
            second["access_token"]
        ),
    )

    assert logout_response.status_code in {
        200,
        204,
    }, logout_response.text

    first_refresh = await client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": first["refresh_token"],
        },
    )

    second_refresh = await client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": second["refresh_token"],
        },
    )

    assert first_refresh.status_code in {
        400,
        401,
        403,
        409,
    }, first_refresh.text

    assert second_refresh.status_code in {
        400,
        401,
        403,
        409,
    }, second_refresh.text


# =========================================================
# LOGOUT-ALL DOES NOT AFFECT OTHER USER
# =========================================================


@pytest.mark.asyncio
async def test_logout_all_does_not_revoke_other_users_sessions(
    client: AsyncClient,
    db_session,
    test_user_payload,
    second_test_user_payload,
):
    first_user_data = await create_logged_in_user(
        client,
        test_user_payload,
    )

    second_user_data = await create_logged_in_user(
        client,
        second_test_user_payload,
    )

    logout_response = await client.post(
        "/api/v1/auth/logout-all",
        headers=bearer_headers(
            first_user_data["access_token"]
        ),
    )

    assert logout_response.status_code in {
        200,
        204,
    }, logout_response.text

    await db_session.rollback()

    first_user = await get_user_by_email(
        db_session,
        test_user_payload["email"],
    )

    first_user_id = first_user.id

    second_user = await get_user_by_email(
        db_session,
        second_test_user_payload["email"],
    )

    second_user_id = second_user.id

    first_sessions = await get_user_sessions(
        db_session,
        first_user_id,
    )

    second_sessions = await get_user_sessions(
        db_session,
        second_user_id,
    )

    assert len(first_sessions) == 1
    assert len(second_sessions) == 1

    assert first_sessions[0].revoked_at is not None
    assert second_sessions[0].revoked_at is None

    second_refresh = await client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": second_user_data["refresh_token"],
        },
    )

    assert second_refresh.status_code == 200, second_refresh.text


# =========================================================
# LOGIN AFTER LOGOUT-ALL CREATES NEW ACTIVE SESSION
# =========================================================


@pytest.mark.asyncio
async def test_login_after_logout_all_creates_new_active_session(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    original = await create_logged_in_user(
        client,
        test_user_payload,
    )

    logout_response = await client.post(
        "/api/v1/auth/logout-all",
        headers=bearer_headers(
            original["access_token"]
        ),
    )

    assert logout_response.status_code in {
        200,
        204,
    }, logout_response.text

    new_login = await login_user(
        client,
        test_user_payload,
    )

    assert new_login["access_token"]
    assert new_login["refresh_token"]

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

    revoked_sessions = [
        session
        for session in sessions
        if session.revoked_at is not None
    ]

    assert len(active_sessions) == 1
    assert len(revoked_sessions) == 1


# =========================================================
# SECOND LOGOUT WITH SAME TOKEN
# =========================================================


@pytest.mark.asyncio
async def test_second_logout_with_same_refresh_token_is_safe(
    client: AsyncClient,
    test_user_payload,
):
    data = await create_logged_in_user(
        client,
        test_user_payload,
    )

    refresh_token = data["refresh_token"]

    first_response = await client.post(
        "/api/v1/auth/logout",
        json={
            "refresh_token": refresh_token,
        },
    )

    assert first_response.status_code in {
        200,
        204,
    }, first_response.text

    second_response = await client.post(
        "/api/v1/auth/logout",
        json={
            "refresh_token": refresh_token,
        },
    )

    assert second_response.status_code in {
        200,
        204,
        400,
        401,
        409,
    }, second_response.text


# =========================================================
# LOGOUT ACCESS TOKEN CANNOT BE USED AS REFRESH TOKEN
# =========================================================


@pytest.mark.asyncio
async def test_logout_rejects_access_token_as_refresh_token(
    client: AsyncClient,
    test_user_payload,
):
    data = await create_logged_in_user(
        client,
        test_user_payload,
    )

    response = await client.post(
        "/api/v1/auth/logout",
        json={
            "refresh_token": data["access_token"],
        },
    )

    assert response.status_code in {
        400,
        401,
        403,
        422,
    }, response.text


# =========================================================
# LOGOUT DOES NOT REVOKE DIFFERENT SESSION TOKEN
# =========================================================


@pytest.mark.asyncio
async def test_logout_keeps_other_refresh_token_usable(
    client: AsyncClient,
    test_user_payload,
):
    await signup_and_verify(
        client,
        test_user_payload,
    )

    first = await login_user(
        client,
        test_user_payload,
    )

    second = await login_user(
        client,
        test_user_payload,
    )

    logout_response = await client.post(
        "/api/v1/auth/logout",
        json={
            "refresh_token": first["refresh_token"],
        },
    )

    assert logout_response.status_code in {
        200,
        204,
    }, logout_response.text

    second_refresh_response = await client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": second["refresh_token"],
        },
    )

    assert second_refresh_response.status_code == 200, (
        second_refresh_response.text
    )