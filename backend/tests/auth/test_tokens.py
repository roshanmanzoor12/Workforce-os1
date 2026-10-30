from __future__ import annotations

from datetime import datetime, timezone

import jwt
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
) -> dict:
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "identifier": payload["email"],
            "password": payload["password"],
            "remember_me": False,
        },
    )

    assert response.status_code == 200, response.text

    return response.json()


async def create_logged_in_user(
    client: AsyncClient,
    payload: dict,
) -> dict:
    await signup_and_verify(
        client,
        payload,
    )

    return await login_user(
        client,
        payload,
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


async def get_refresh_sessions(
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


def decode_without_verification(
    token: str,
) -> dict:
    """
    Decode JWT only for inspecting claims inside tests.

    IMPORTANT:
    This helper deliberately does NOT verify the signature.

    Actual signature validation is tested through real protected
    API endpoints later in this file.
    """

    return jwt.decode(
        token,
        options={
            "verify_signature": False,
            "verify_exp": False,
            "verify_aud": False,
        },
    )


def tamper_token(
    token: str,
) -> str:
    parts = token.split(".")

    assert len(parts) == 3

    payload = parts[1]

    assert len(payload) >= 3

    index = len(payload) // 2

    original = payload[index]

    replacement = (
        "a"
        if original != "a"
        else "b"
    )

    parts[1] = (
        payload[:index]
        + replacement
        + payload[index + 1:]
    )

    return ".".join(parts)


def extract_user_from_me_response(
    data: dict,
) -> dict:
    """
    Support both possible /me response shapes:

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


def extract_token_type(
    payload: dict,
):
    """
    Support either token claim naming convention:

        type
        token_type
    """

    return (
        payload.get("type")
        or payload.get("token_type")
    )


# =========================================================
# LOGIN RETURNS BOTH TOKEN TYPES
# =========================================================


@pytest.mark.asyncio
async def test_login_returns_access_and_refresh_tokens(
    client: AsyncClient,
    test_user_payload,
):
    data = await create_logged_in_user(
        client,
        test_user_payload,
    )

    assert data["access_token"]
    assert data["refresh_token"]

    assert isinstance(
        data["access_token"],
        str,
    )

    assert isinstance(
        data["refresh_token"],
        str,
    )

    assert (
        data["access_token"]
        != data["refresh_token"]
    )


# =========================================================
# ACCESS TOKEN JWT STRUCTURE
# =========================================================


@pytest.mark.asyncio
async def test_access_token_has_valid_jwt_structure(
    client: AsyncClient,
    test_user_payload,
):
    data = await create_logged_in_user(
        client,
        test_user_payload,
    )

    access_token = data["access_token"]

    parts = access_token.split(".")

    assert len(parts) == 3

    payload = decode_without_verification(
        access_token
    )

    assert isinstance(payload, dict)


# =========================================================
# REFRESH TOKEN JWT STRUCTURE
# =========================================================


@pytest.mark.asyncio
async def test_refresh_token_has_valid_jwt_structure(
    client: AsyncClient,
    test_user_payload,
):
    data = await create_logged_in_user(
        client,
        test_user_payload,
    )

    refresh_token = data["refresh_token"]

    assert len(
        refresh_token.split(".")
    ) == 3

    payload = decode_without_verification(
        refresh_token
    )

    assert isinstance(payload, dict)


# =========================================================
# ACCESS TOKEN SUBJECT
# =========================================================


@pytest.mark.asyncio
async def test_access_token_contains_subject(
    client: AsyncClient,
    test_user_payload,
):
    data = await create_logged_in_user(
        client,
        test_user_payload,
    )

    payload = decode_without_verification(
        data["access_token"]
    )

    assert "sub" in payload
    assert payload["sub"]


# =========================================================
# REFRESH TOKEN SUBJECT
# =========================================================


@pytest.mark.asyncio
async def test_refresh_token_contains_subject(
    client: AsyncClient,
    test_user_payload,
):
    data = await create_logged_in_user(
        client,
        test_user_payload,
    )

    payload = decode_without_verification(
        data["refresh_token"]
    )

    assert "sub" in payload
    assert payload["sub"]


# =========================================================
# SAME USER SUBJECT
# =========================================================


@pytest.mark.asyncio
async def test_access_and_refresh_tokens_reference_same_user(
    client: AsyncClient,
    test_user_payload,
):
    data = await create_logged_in_user(
        client,
        test_user_payload,
    )

    access_payload = decode_without_verification(
        data["access_token"]
    )

    refresh_payload = decode_without_verification(
        data["refresh_token"]
    )

    assert (
        access_payload["sub"]
        == refresh_payload["sub"]
    )


# =========================================================
# ACCESS TOKEN EXPIRATION
# =========================================================


@pytest.mark.asyncio
async def test_access_token_contains_expiration(
    client: AsyncClient,
    test_user_payload,
):
    data = await create_logged_in_user(
        client,
        test_user_payload,
    )

    payload = decode_without_verification(
        data["access_token"]
    )

    assert "exp" in payload

    exp = int(
        payload["exp"]
    )

    now = int(
        datetime.now(
            timezone.utc
        ).timestamp()
    )

    assert exp > now


# =========================================================
# REFRESH TOKEN EXPIRATION
# =========================================================


@pytest.mark.asyncio
async def test_refresh_token_contains_expiration(
    client: AsyncClient,
    test_user_payload,
):
    data = await create_logged_in_user(
        client,
        test_user_payload,
    )

    payload = decode_without_verification(
        data["refresh_token"]
    )

    assert "exp" in payload

    exp = int(
        payload["exp"]
    )

    now = int(
        datetime.now(
            timezone.utc
        ).timestamp()
    )

    assert exp > now


# =========================================================
# REFRESH TOKEN LASTS LONGER
# =========================================================


@pytest.mark.asyncio
async def test_refresh_token_expires_after_access_token(
    client: AsyncClient,
    test_user_payload,
):
    data = await create_logged_in_user(
        client,
        test_user_payload,
    )

    access_payload = decode_without_verification(
        data["access_token"]
    )

    refresh_payload = decode_without_verification(
        data["refresh_token"]
    )

    assert (
        int(refresh_payload["exp"])
        > int(access_payload["exp"])
    )


# =========================================================
# TOKEN TYPE CLAIMS
# =========================================================


@pytest.mark.asyncio
async def test_access_and_refresh_tokens_have_different_types(
    client: AsyncClient,
    test_user_payload,
):
    data = await create_logged_in_user(
        client,
        test_user_payload,
    )

    access_payload = decode_without_verification(
        data["access_token"]
    )

    refresh_payload = decode_without_verification(
        data["refresh_token"]
    )

    access_type = extract_token_type(
        access_payload
    )

    refresh_type = extract_token_type(
        refresh_payload
    )

    assert access_type is not None
    assert refresh_type is not None

    assert access_type != refresh_type

    assert "access" in str(
        access_type
    ).lower()

    assert "refresh" in str(
        refresh_type
    ).lower()


# =========================================================
# REFRESH TOKEN HAS JTI
# =========================================================


@pytest.mark.asyncio
async def test_refresh_token_contains_jti(
    client: AsyncClient,
    test_user_payload,
):
    data = await create_logged_in_user(
        client,
        test_user_payload,
    )

    payload = decode_without_verification(
        data["refresh_token"]
    )

    assert "jti" in payload
    assert payload["jti"]


# =========================================================
# JTI MATCHES DATABASE SESSION
# =========================================================


@pytest.mark.asyncio
async def test_refresh_token_jti_matches_database_session(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    data = await create_logged_in_user(
        client,
        test_user_payload,
    )

    refresh_payload = decode_without_verification(
        data["refresh_token"]
    )

    refresh_jti = str(
        refresh_payload["jti"]
    )

    await db_session.rollback()

    user = await get_user_by_email(
        db_session,
        test_user_payload["email"],
    )

    user_id = user.id

    sessions = await get_refresh_sessions(
        db_session,
        user_id,
    )

    assert len(sessions) == 1

    session = sessions[0]

    assert session.jti == refresh_jti


# =========================================================
# REFRESH TOKEN HASH ONLY IN DATABASE
# =========================================================


@pytest.mark.asyncio
async def test_refresh_token_is_not_stored_plaintext(
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

    sessions = await get_refresh_sessions(
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
# ACCESS TOKEN WORKS ON /ME
# =========================================================


@pytest.mark.asyncio
async def test_access_token_authenticates_me_endpoint(
    client: AsyncClient,
    test_user_payload,
):
    data = await create_logged_in_user(
        client,
        test_user_payload,
    )

    response = await client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": (
                f"Bearer {data['access_token']}"
            )
        },
    )

    assert response.status_code == 200, response.text

    me_data = extract_user_from_me_response(
        response.json()
    )

    assert (
        me_data["email"]
        == test_user_payload["email"]
    )

    assert (
        me_data["username"]
        == test_user_payload["username"]
    )


# =========================================================
# REFRESH TOKEN MUST NOT WORK AS ACCESS TOKEN
# =========================================================


@pytest.mark.asyncio
async def test_refresh_token_cannot_authenticate_me_endpoint(
    client: AsyncClient,
    test_user_payload,
):
    data = await create_logged_in_user(
        client,
        test_user_payload,
    )

    response = await client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": (
                f"Bearer {data['refresh_token']}"
            )
        },
    )

    assert response.status_code in {
        401,
        403,
    }, response.text


# =========================================================
# ACCESS TOKEN MUST NOT WORK AS REFRESH TOKEN
# =========================================================


@pytest.mark.asyncio
async def test_access_token_cannot_be_used_for_refresh(
    client: AsyncClient,
    test_user_payload,
):
    data = await create_logged_in_user(
        client,
        test_user_payload,
    )

    response = await client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": data[
                "access_token"
            ],
        },
    )

    assert response.status_code in {
        400,
        401,
        403,
        422,
    }, response.text


# =========================================================
# VALID REFRESH TOKEN ROTATION
# =========================================================


@pytest.mark.asyncio
async def test_valid_refresh_token_rotates_tokens(
    client: AsyncClient,
    test_user_payload,
):
    data = await create_logged_in_user(
        client,
        test_user_payload,
    )

    old_access_token = data[
        "access_token"
    ]

    old_refresh_token = data[
        "refresh_token"
    ]

    response = await client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": old_refresh_token,
        },
    )

    assert response.status_code == 200, response.text

    refreshed = response.json()

    assert refreshed["access_token"]
    assert refreshed["refresh_token"]

    assert (
        refreshed["access_token"]
        != old_access_token
    )

    assert (
        refreshed["refresh_token"]
        != old_refresh_token
    )


# =========================================================
# OLD REFRESH SESSION IS REVOKED
# =========================================================


@pytest.mark.asyncio
async def test_refresh_rotation_revokes_old_session(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    data = await create_logged_in_user(
        client,
        test_user_payload,
    )

    old_refresh_token = data[
        "refresh_token"
    ]

    old_payload = decode_without_verification(
        old_refresh_token
    )

    old_jti = str(
        old_payload["jti"]
    )

    response = await client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": old_refresh_token,
        },
    )

    assert response.status_code == 200, response.text

    await db_session.rollback()

    result = await db_session.execute(
        select(RefreshSession).where(
            RefreshSession.jti == old_jti
        )
    )

    old_session = result.scalar_one_or_none()

    assert old_session is not None

    assert old_session.revoked_at is not None
    assert old_session.rotated_at is not None


# =========================================================
# ROTATION CREATES REPLACEMENT SESSION
# =========================================================


@pytest.mark.asyncio
async def test_refresh_rotation_creates_replacement_session(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    data = await create_logged_in_user(
        client,
        test_user_payload,
    )

    old_refresh_token = data[
        "refresh_token"
    ]

    response = await client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": old_refresh_token,
        },
    )

    assert response.status_code == 200, response.text

    refreshed = response.json()

    new_payload = decode_without_verification(
        refreshed["refresh_token"]
    )

    new_jti = str(
        new_payload["jti"]
    )

    await db_session.rollback()

    result = await db_session.execute(
        select(RefreshSession).where(
            RefreshSession.jti == new_jti
        )
    )

    new_session = result.scalar_one_or_none()

    assert new_session is not None

    assert new_session.revoked_at is None
    assert new_session.rotated_at is None


# =========================================================
# REPLACEMENT SESSION LINKAGE
# =========================================================


@pytest.mark.asyncio
async def test_rotated_session_links_to_replacement(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    data = await create_logged_in_user(
        client,
        test_user_payload,
    )

    old_payload = decode_without_verification(
        data["refresh_token"]
    )

    old_jti = str(
        old_payload["jti"]
    )

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

    result = await db_session.execute(
        select(RefreshSession).where(
            RefreshSession.jti == old_jti
        )
    )

    old_session = result.scalar_one()

    assert old_session.replaced_by_session_id is not None


# =========================================================
# OLD REFRESH TOKEN CANNOT BE REUSED
# =========================================================


@pytest.mark.asyncio
async def test_old_refresh_token_cannot_be_reused(
    client: AsyncClient,
    test_user_payload,
):
    data = await create_logged_in_user(
        client,
        test_user_payload,
    )

    old_refresh_token = data[
        "refresh_token"
    ]

    first_response = await client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": old_refresh_token,
        },
    )

    assert first_response.status_code == 200, first_response.text

    second_response = await client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": old_refresh_token,
        },
    )

    assert second_response.status_code in {
        400,
        401,
        403,
        409,
    }, second_response.text


# =========================================================
# NEW REFRESH TOKEN CAN ROTATE AGAIN
# =========================================================


@pytest.mark.asyncio
async def test_replacement_refresh_token_can_rotate_again(
    client: AsyncClient,
    test_user_payload,
):
    data = await create_logged_in_user(
        client,
        test_user_payload,
    )

    first_rotation = await client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": data[
                "refresh_token"
            ],
        },
    )

    assert first_rotation.status_code == 200, first_rotation.text

    first_data = first_rotation.json()

    second_rotation = await client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": first_data[
                "refresh_token"
            ],
        },
    )

    assert second_rotation.status_code == 200, second_rotation.text

    second_data = second_rotation.json()

    assert second_data["access_token"]
    assert second_data["refresh_token"]

    assert (
        second_data["refresh_token"]
        != first_data["refresh_token"]
    )


# =========================================================
# SECOND ROTATION REVOKES FIRST REPLACEMENT
# =========================================================


@pytest.mark.asyncio
async def test_second_refresh_rotation_revokes_previous_session(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    data = await create_logged_in_user(
        client,
        test_user_payload,
    )

    first_rotation = await client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": data[
                "refresh_token"
            ],
        },
    )

    assert first_rotation.status_code == 200, first_rotation.text

    first_data = first_rotation.json()

    first_replacement_payload = decode_without_verification(
        first_data["refresh_token"]
    )

    first_replacement_jti = str(
        first_replacement_payload["jti"]
    )

    second_rotation = await client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": first_data[
                "refresh_token"
            ],
        },
    )

    assert second_rotation.status_code == 200, second_rotation.text

    await db_session.rollback()

    result = await db_session.execute(
        select(RefreshSession).where(
            RefreshSession.jti == first_replacement_jti
        )
    )

    first_replacement_session = result.scalar_one_or_none()

    assert first_replacement_session is not None
    assert first_replacement_session.revoked_at is not None
    assert first_replacement_session.rotated_at is not None


# =========================================================
# REFRESH ROTATION CREATES DIFFERENT JTI
# =========================================================


@pytest.mark.asyncio
async def test_refresh_rotation_creates_new_jti(
    client: AsyncClient,
    test_user_payload,
):
    data = await create_logged_in_user(
        client,
        test_user_payload,
    )

    old_payload = decode_without_verification(
        data["refresh_token"]
    )

    response = await client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": data[
                "refresh_token"
            ],
        },
    )

    assert response.status_code == 200, response.text

    refreshed = response.json()

    new_payload = decode_without_verification(
        refreshed["refresh_token"]
    )

    assert old_payload["jti"]
    assert new_payload["jti"]

    assert (
        old_payload["jti"]
        != new_payload["jti"]
    )


# =========================================================
# TAMPERED ACCESS TOKEN
# =========================================================


@pytest.mark.asyncio
async def test_tampered_access_token_rejected(
    client: AsyncClient,
    test_user_payload,
):
    data = await create_logged_in_user(
        client,
        test_user_payload,
    )

    tampered = tamper_token(
        data["access_token"]
    )

    response = await client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": (
                f"Bearer {tampered}"
            )
        },
    )

    assert response.status_code in {
        401,
        403,
    }, response.text


# =========================================================
# TAMPERED REFRESH TOKEN
# =========================================================


@pytest.mark.asyncio
async def test_tampered_refresh_token_rejected(
    client: AsyncClient,
    test_user_payload,
):
    data = await create_logged_in_user(
        client,
        test_user_payload,
    )

    tampered = tamper_token(
        data["refresh_token"]
    )

    response = await client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": tampered,
        },
    )

    assert response.status_code in {
        400,
        401,
        403,
        422,
    }, response.text


# =========================================================
# MALFORMED ACCESS TOKEN
# =========================================================


@pytest.mark.asyncio
async def test_malformed_access_token_rejected(
    client: AsyncClient,
):
    response = await client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": (
                "Bearer definitely-not-a-jwt"
            )
        },
    )

    assert response.status_code in {
        401,
        403,
    }, response.text


# =========================================================
# MALFORMED REFRESH TOKEN
# =========================================================


@pytest.mark.asyncio
async def test_malformed_refresh_token_rejected(
    client: AsyncClient,
):
    response = await client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": (
                "definitely-not-a-jwt"
            ),
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
async def test_empty_refresh_token_rejected(
    client: AsyncClient,
):
    response = await client.post(
        "/api/v1/auth/refresh",
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
# MISSING REFRESH TOKEN
# =========================================================


@pytest.mark.asyncio
async def test_missing_refresh_token_rejected(
    client: AsyncClient,
):
    response = await client.post(
        "/api/v1/auth/refresh",
        json={},
    )

    assert response.status_code == 422, response.text


# =========================================================
# NO TOKEN CANNOT ACCESS /ME
# =========================================================


@pytest.mark.asyncio
async def test_no_token_cannot_access_me(
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
# RANDOM BEARER TOKEN CANNOT ACCESS /ME
# =========================================================


@pytest.mark.asyncio
async def test_random_bearer_token_cannot_access_me(
    client: AsyncClient,
):
    response = await client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": (
                "Bearer random-non-jwt-token"
            ),
        },
    )

    assert response.status_code in {
        401,
        403,
    }, response.text