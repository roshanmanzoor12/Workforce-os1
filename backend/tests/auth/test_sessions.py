from __future__ import annotations

from uuid import UUID

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

    return response.json()


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
        "Authorization": (
            f"Bearer {access_token}"
        )
    }


def extract_sessions(
    payload,
) -> list[dict]:
    """
    Support common API response shapes:

        [
            {...},
            {...},
        ]

    or:

        {
            "sessions": [...]
        }

    or:

        {
            "items": [...]
        }
    """

    if isinstance(payload, list):
        return payload

    if not isinstance(payload, dict):
        return []

    sessions = payload.get("sessions")

    if isinstance(sessions, list):
        return sessions

    items = payload.get("items")

    if isinstance(items, list):
        return items

    return []


def get_response_session_id(
    session: dict,
) -> str | None:
    value = (
        session.get("id")
        or session.get("session_id")
    )

    if value is None:
        return None

    return str(value)


# =========================================================
# GET /SESSIONS REQUIRES AUTH
# =========================================================


@pytest.mark.asyncio
async def test_sessions_endpoint_requires_authentication(
    client: AsyncClient,
):
    response = await client.get(
        "/api/v1/auth/sessions",
    )

    assert response.status_code in {
        401,
        403,
    }, response.text


# =========================================================
# INVALID TOKEN CANNOT LIST SESSIONS
# =========================================================


@pytest.mark.asyncio
async def test_invalid_token_cannot_list_sessions(
    client: AsyncClient,
):
    response = await client.get(
        "/api/v1/auth/sessions",
        headers={
            "Authorization": (
                "Bearer invalid.jwt.token"
            )
        },
    )

    assert response.status_code in {
        401,
        403,
    }, response.text


# =========================================================
# LOGIN CREATES ONE SESSION
# =========================================================


@pytest.mark.asyncio
async def test_login_creates_one_active_session(
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

    session = sessions[0]

    assert session.revoked_at is None
    assert session.expires_at is not None
    assert session.jti
    assert session.token_hash

    assert data["access_token"]
    assert data["refresh_token"]


# =========================================================
# LIST SESSIONS
# =========================================================


@pytest.mark.asyncio
async def test_authenticated_user_can_list_sessions(
    client: AsyncClient,
    test_user_payload,
):
    data = await create_logged_in_user(
        client,
        test_user_payload,
    )

    response = await client.get(
        "/api/v1/auth/sessions",
        headers=bearer_headers(
            data["access_token"]
        ),
    )

    assert response.status_code == 200, response.text

    sessions = extract_sessions(
        response.json()
    )

    assert len(sessions) >= 1


# =========================================================
# SESSION LIST CONTAINS CURRENT SESSION
# =========================================================


@pytest.mark.asyncio
async def test_session_list_contains_login_session(
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

    db_sessions = await get_user_sessions(
        db_session,
        user_id,
    )

    assert len(db_sessions) == 1

    expected_session_id = str(
        db_sessions[0].id
    )

    response = await client.get(
        "/api/v1/auth/sessions",
        headers=bearer_headers(
            data["access_token"]
        ),
    )

    assert response.status_code == 200, response.text

    api_sessions = extract_sessions(
        response.json()
    )

    ids = {
        get_response_session_id(item)
        for item in api_sessions
    }

    assert expected_session_id in ids


# =========================================================
# MULTIPLE LOGINS CREATE MULTIPLE SESSIONS
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

    first = await login_user(
        client,
        test_user_payload,
        user_agent="WorkforceOS-Test-Desktop",
    )

    second = await login_user(
        client,
        test_user_payload,
        user_agent="WorkforceOS-Test-Mobile",
    )

    assert first["access_token"]
    assert second["access_token"]

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
# SESSION METADATA STORED
# =========================================================


@pytest.mark.asyncio
async def test_session_stores_user_agent(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    expected_user_agent = (
        "WorkforceOS-Desktop-Test/1.0"
    )

    await create_logged_in_user(
        client,
        test_user_payload,
        user_agent=expected_user_agent,
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

    session = sessions[0]

    assert session.user_agent
    assert expected_user_agent in session.user_agent


# =========================================================
# SESSION HAS IP
# =========================================================


@pytest.mark.asyncio
async def test_session_stores_ip_address_when_available(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    await create_logged_in_user(
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

    session = sessions[0]

    assert (
        session.ip_address is None
        or isinstance(
            session.ip_address,
            str,
        )
    )


# =========================================================
# SESSION TOKEN HASH NOT PLAINTEXT
# =========================================================


@pytest.mark.asyncio
async def test_session_does_not_store_plaintext_refresh_token(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    data = await create_logged_in_user(
        client,
        test_user_payload,
    )

    refresh_token = data[
        "refresh_token"
    ]

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

    assert (
        session.token_hash
        != refresh_token
    )

    assert (
        refresh_token
        not in session.token_hash
    )


# =========================================================
# REVOKE SINGLE SESSION
# =========================================================


@pytest.mark.asyncio
async def test_user_can_revoke_own_session(
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

    response = await client.delete(
        f"/api/v1/auth/sessions/{session_id}",
        headers=bearer_headers(
            data["access_token"]
        ),
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
# REVOKING SESSION DOES NOT DELETE RECORD
# =========================================================


@pytest.mark.asyncio
async def test_revoked_session_record_is_preserved(
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

    response = await client.delete(
        f"/api/v1/auth/sessions/{session_id}",
        headers=bearer_headers(
            data["access_token"]
        ),
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
# REVOKE ONE OF MULTIPLE SESSIONS
# =========================================================


@pytest.mark.asyncio
async def test_revoke_one_session_does_not_revoke_other_sessions(
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
        user_agent="First-Device",
    )

    second_login = await login_user(
        client,
        test_user_payload,
        user_agent="Second-Device",
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

    # IMPORTANT:
    # Save plain UUID values BEFORE rollback.
    #
    # Do not access ORM objects after rollback because SQLAlchemy
    # may expire their attributes and trigger MissingGreenlet.
    first_session_id = sessions[0].id
    second_session_id = sessions[1].id

    response = await client.delete(
        f"/api/v1/auth/sessions/{first_session_id}",
        headers=bearer_headers(
            second_login["access_token"]
        ),
    )

    assert response.status_code in {
        200,
        204,
    }, response.text

    await db_session.rollback()

    first_db_session = await get_session_by_id(
        db_session,
        first_session_id,
    )

    second_db_session = await get_session_by_id(
        db_session,
        second_session_id,
    )

    assert first_db_session is not None
    assert second_db_session is not None

    assert first_db_session.revoked_at is not None
    assert second_db_session.revoked_at is None

    assert first_login["refresh_token"]
    assert second_login["refresh_token"]


# =========================================================
# CANNOT REVOKE SESSION WITHOUT AUTH
# =========================================================


@pytest.mark.asyncio
async def test_session_revoke_requires_authentication(
    client: AsyncClient,
):
    fake_session_id = (
        "00000000-0000-0000-0000-000000000001"
    )

    response = await client.delete(
        f"/api/v1/auth/sessions/{fake_session_id}",
    )

    assert response.status_code in {
        401,
        403,
    }, response.text


# =========================================================
# INVALID SESSION UUID
# =========================================================


@pytest.mark.asyncio
async def test_invalid_session_id_is_rejected(
    client: AsyncClient,
    test_user_payload,
):
    data = await create_logged_in_user(
        client,
        test_user_payload,
    )

    response = await client.delete(
        "/api/v1/auth/sessions/not-a-valid-uuid",
        headers=bearer_headers(
            data["access_token"]
        ),
    )

    assert response.status_code in {
        404,
        422,
    }, response.text


# =========================================================
# UNKNOWN SESSION
# =========================================================


@pytest.mark.asyncio
async def test_unknown_session_is_rejected(
    client: AsyncClient,
    test_user_payload,
):
    data = await create_logged_in_user(
        client,
        test_user_payload,
    )

    unknown_session_id = (
        "00000000-0000-0000-0000-000000000001"
    )

    response = await client.delete(
        f"/api/v1/auth/sessions/{unknown_session_id}",
        headers=bearer_headers(
            data["access_token"]
        ),
    )

    assert response.status_code in {
        404,
        422,
    }, response.text


# =========================================================
# USER CANNOT REVOKE ANOTHER USER'S SESSION
# =========================================================


@pytest.mark.asyncio
async def test_user_cannot_revoke_another_users_session(
    client: AsyncClient,
    db_session,
    test_user_payload,
    second_test_user_payload,
):
    """
    Verify user A cannot revoke a refresh session that belongs
    to user B.

    NOTE:
    conftest.py exposes the fixture as:
        second_test_user_payload

    not:
        second_user_payload
    """

    first_data = await create_logged_in_user(
        client,
        test_user_payload,
    )

    second_data = await create_logged_in_user(
        client,
        second_test_user_payload,
    )

    assert first_data["access_token"]
    assert second_data["access_token"]

    await db_session.rollback()

    second_user = await get_user_by_email(
        db_session,
        second_test_user_payload["email"],
    )

    second_user_id = second_user.id

    second_sessions = await get_user_sessions(
        db_session,
        second_user_id,
    )

    assert len(second_sessions) == 1

    # Store scalar before any subsequent rollback.
    target_session_id = (
        second_sessions[0].id
    )

    response = await client.delete(
        f"/api/v1/auth/sessions/{target_session_id}",
        headers=bearer_headers(
            first_data["access_token"]
        ),
    )

    assert response.status_code in {
        403,
        404,
    }, response.text

    await db_session.rollback()

    target_session = await get_session_by_id(
        db_session,
        target_session_id,
    )

    assert target_session is not None
    assert target_session.revoked_at is None


# =========================================================
# REFRESH ROTATION PRESERVES SESSION HISTORY
# =========================================================


@pytest.mark.asyncio
async def test_refresh_rotation_preserves_old_session_record(
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

    initial_sessions = await get_user_sessions(
        db_session,
        user_id,
    )

    assert len(initial_sessions) == 1

    old_session_id = initial_sessions[0].id

    await db_session.rollback()

    response = await client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": data[
                "refresh_token"
            ],
        },
    )

    assert response.status_code == 200, response.text

    await db_session.rollback()

    old_session = await get_session_by_id(
        db_session,
        old_session_id,
    )

    assert old_session is not None
    assert old_session.revoked_at is not None
    assert old_session.rotated_at is not None
    assert old_session.replaced_by_session_id is not None


# =========================================================
# REFRESH ROTATION CREATES NEW ACTIVE SESSION
# =========================================================


@pytest.mark.asyncio
async def test_refresh_rotation_creates_new_active_session(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    data = await create_logged_in_user(
        client,
        test_user_payload,
    )

    refresh_response = await client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": data[
                "refresh_token"
            ],
        },
    )

    assert refresh_response.status_code == 200, refresh_response.text

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

    rotated_sessions = [
        session
        for session in sessions
        if session.rotated_at is not None
    ]

    assert len(active_sessions) == 1
    assert len(rotated_sessions) == 1


# =========================================================
# SESSION IDS ARE UNIQUE
# =========================================================


@pytest.mark.asyncio
async def test_multiple_sessions_have_unique_ids(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    await signup_and_verify(
        client,
        test_user_payload,
    )

    await login_user(
        client,
        test_user_payload,
    )

    await login_user(
        client,
        test_user_payload,
    )

    await login_user(
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

    assert len(sessions) == 3

    session_ids = {
        str(session.id)
        for session in sessions
    }

    assert len(session_ids) == 3


# =========================================================
# SESSION JTIS ARE UNIQUE
# =========================================================


@pytest.mark.asyncio
async def test_multiple_sessions_have_unique_jtis(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    await signup_and_verify(
        client,
        test_user_payload,
    )

    await login_user(
        client,
        test_user_payload,
    )

    await login_user(
        client,
        test_user_payload,
    )

    await login_user(
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

    assert len(sessions) == 3

    jtis = {
        session.jti
        for session in sessions
    }

    assert len(jtis) == 3


# =========================================================
# SESSION IDS ARE UUIDS
# =========================================================


@pytest.mark.asyncio
async def test_session_ids_are_valid_uuids(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    await create_logged_in_user(
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

    session_id = str(
        sessions[0].id
    )

    parsed = UUID(
        session_id
    )

    assert str(parsed) == session_id


# =========================================================
# REVOKED SESSION APPEARS REVOKED IN DB
# =========================================================


@pytest.mark.asyncio
async def test_revocation_timestamp_is_persisted(
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

    response = await client.delete(
        f"/api/v1/auth/sessions/{session_id}",
        headers=bearer_headers(
            data["access_token"]
        ),
    )

    assert response.status_code in {
        200,
        204,
    }, response.text

    await db_session.rollback()

    persisted = await get_session_by_id(
        db_session,
        session_id,
    )

    assert persisted is not None
    assert persisted.revoked_at is not None


# =========================================================
# LIST SESSION RESPONSE DOES NOT EXPOSE TOKEN HASH
# =========================================================


@pytest.mark.asyncio
async def test_session_list_does_not_expose_token_hash(
    client: AsyncClient,
    test_user_payload,
):
    data = await create_logged_in_user(
        client,
        test_user_payload,
    )

    response = await client.get(
        "/api/v1/auth/sessions",
        headers=bearer_headers(
            data["access_token"]
        ),
    )

    assert response.status_code == 200, response.text

    raw_body = response.text.lower()

    assert "token_hash" not in raw_body

    assert (
        data["refresh_token"]
        not in response.text
    )


# =========================================================
# LIST SESSION RESPONSE DOES NOT EXPOSE JTI
# =========================================================


@pytest.mark.asyncio
async def test_session_list_does_not_expose_internal_jti(
    client: AsyncClient,
    test_user_payload,
):
    data = await create_logged_in_user(
        client,
        test_user_payload,
    )

    response = await client.get(
        "/api/v1/auth/sessions",
        headers=bearer_headers(
            data["access_token"]
        ),
    )

    assert response.status_code == 200, response.text

    raw_body = response.text.lower()

    assert '"jti"' not in raw_body


# =========================================================
# REVOKING SAME SESSION TWICE IS SAFE
# =========================================================


@pytest.mark.asyncio
async def test_revoking_same_session_twice_is_safe(
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
    )

    second_login = await login_user(
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

    assert len(sessions) == 2

    target_session_id = sessions[0].id

    headers = bearer_headers(
        second_login["access_token"]
    )

    first_revoke = await client.delete(
        f"/api/v1/auth/sessions/{target_session_id}",
        headers=headers,
    )

    assert first_revoke.status_code in {
        200,
        204,
    }, first_revoke.text

    second_revoke = await client.delete(
        f"/api/v1/auth/sessions/{target_session_id}",
        headers=headers,
    )

    assert second_revoke.status_code in {
        200,
        204,
        404,
        409,
    }, second_revoke.text

    assert first_login["refresh_token"]