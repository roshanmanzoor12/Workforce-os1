from __future__ import annotations

from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.modules.auth.models import (
    EmailVerificationChallenge,
    PasswordResetChallenge,
    RefreshSession,
    User,
)


# =========================================================
# HELPERS
# =========================================================


def extract_user(data: dict) -> dict:
    """
    Auth /me responses may either expose the user directly or wrap it
    inside {"user": {...}}.

    Keep security tests compatible with the established API contract.
    """

    user = data.get("user")

    if isinstance(user, dict):
        return user

    return data


def bearer_headers(access_token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token}",
    }


async def signup_user(
    client: AsyncClient,
    payload: dict,
):
    return await client.post(
        "/api/v1/auth/signup",
        json=payload,
    )


async def verify_email(
    client: AsyncClient,
    *,
    email: str,
    otp: str = "123456",
):
    return await client.post(
        "/api/v1/auth/verify-email",
        json={
            "email": email,
            "otp": otp,
        },
    )


async def create_verified_user(
    client: AsyncClient,
    payload: dict,
):
    signup_response = await signup_user(
        client,
        payload,
    )

    assert signup_response.status_code == 201, signup_response.text

    verify_response = await verify_email(
        client,
        email=payload["email"],
    )

    assert verify_response.status_code == 200, verify_response.text


async def login_user(
    client: AsyncClient,
    *,
    identifier: str,
    password: str,
):
    return await client.post(
        "/api/v1/auth/login",
        json={
            "identifier": identifier,
            "password": password,
            "remember_me": False,
        },
    )


async def create_logged_in_user(
    client: AsyncClient,
    payload: dict,
) -> dict:
    await create_verified_user(
        client,
        payload,
    )

    login_response = await login_user(
        client,
        identifier=payload["email"],
        password=payload["password"],
    )

    assert login_response.status_code == 200, login_response.text

    return login_response.json()


async def request_password_reset(
    client: AsyncClient,
    *,
    email: str,
):
    return await client.post(
        "/api/v1/auth/forgot-password",
        json={
            "email": email,
        },
    )


async def verify_reset_otp(
    client: AsyncClient,
    *,
    email: str,
    otp: str = "123456",
):
    return await client.post(
        "/api/v1/auth/verify-reset-otp",
        json={
            "email": email,
            "otp": otp,
        },
    )


# =========================================================
# PROTECTED ENDPOINT AUTHENTICATION
# =========================================================


@pytest.mark.asyncio
async def test_me_requires_authentication(
    client: AsyncClient,
):
    response = await client.get(
        "/api/v1/auth/me",
    )

    assert response.status_code in {
        401,
        403,
    }, response.text


@pytest.mark.asyncio
async def test_sessions_requires_authentication(
    client: AsyncClient,
):
    response = await client.get(
        "/api/v1/auth/sessions",
    )

    assert response.status_code in {
        401,
        403,
    }, response.text


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
# INVALID / TAMPERED BEARER TOKENS
# =========================================================


@pytest.mark.asyncio
async def test_random_bearer_token_cannot_access_me(
    client: AsyncClient,
):
    response = await client.get(
        "/api/v1/auth/me",
        headers=bearer_headers(
            "definitely-not-a-valid-jwt"
        ),
    )

    assert response.status_code in {
        401,
        403,
    }, response.text


@pytest.mark.asyncio
async def test_tampered_access_token_is_rejected(
    client: AsyncClient,
    test_user_payload,
):
    login_data = await create_logged_in_user(
        client,
        test_user_payload,
    )

    access_token = login_data["access_token"]

    tampered_token = (
        access_token[:-1]
        + (
            "a"
            if access_token[-1] != "a"
            else "b"
        )
    )

    response = await client.get(
        "/api/v1/auth/me",
        headers=bearer_headers(
            tampered_token
        ),
    )

    assert response.status_code in {
        401,
        403,
    }, response.text


# =========================================================
# TOKEN TYPE SEPARATION
# =========================================================


@pytest.mark.asyncio
async def test_refresh_token_cannot_be_used_as_access_token(
    client: AsyncClient,
    test_user_payload,
):
    login_data = await create_logged_in_user(
        client,
        test_user_payload,
    )

    response = await client.get(
        "/api/v1/auth/me",
        headers=bearer_headers(
            login_data["refresh_token"]
        ),
    )

    assert response.status_code in {
        401,
        403,
    }, response.text


@pytest.mark.asyncio
async def test_access_token_cannot_be_used_for_refresh(
    client: AsyncClient,
    test_user_payload,
):
    login_data = await create_logged_in_user(
        client,
        test_user_payload,
    )

    response = await client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": login_data[
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


@pytest.mark.asyncio
async def test_access_token_cannot_be_used_for_logout_refresh_field(
    client: AsyncClient,
    test_user_payload,
):
    login_data = await create_logged_in_user(
        client,
        test_user_payload,
    )

    response = await client.post(
        "/api/v1/auth/logout",
        json={
            "refresh_token": login_data[
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
# PASSWORD HASH / USER INTERNALS MUST NOT LEAK
# =========================================================


@pytest.mark.asyncio
async def test_signup_response_does_not_expose_password_hash(
    client: AsyncClient,
    test_user_payload,
):
    response = await signup_user(
        client,
        test_user_payload,
    )

    assert response.status_code == 201, response.text

    body = response.text.lower()

    assert "password_hash" not in body
    assert "hashed_password" not in body
    assert test_user_payload["password"].lower() not in body


@pytest.mark.asyncio
async def test_login_response_does_not_expose_password_hash(
    client: AsyncClient,
    test_user_payload,
):
    login_data = await create_logged_in_user(
        client,
        test_user_payload,
    )

    body = str(login_data).lower()

    assert "password_hash" not in body
    assert "hashed_password" not in body
    assert test_user_payload["password"].lower() not in body


@pytest.mark.asyncio
async def test_me_response_does_not_expose_password_hash(
    client: AsyncClient,
    test_user_payload,
):
    login_data = await create_logged_in_user(
        client,
        test_user_payload,
    )

    response = await client.get(
        "/api/v1/auth/me",
        headers=bearer_headers(
            login_data["access_token"]
        ),
    )

    assert response.status_code == 200, response.text

    body = response.text.lower()

    assert "password_hash" not in body
    assert "hashed_password" not in body
    assert test_user_payload["password"].lower() not in body


# =========================================================
# SESSION INTERNALS MUST NOT LEAK
# =========================================================


@pytest.mark.asyncio
async def test_session_api_does_not_expose_token_hash_or_jti(
    client: AsyncClient,
    test_user_payload,
):
    login_data = await create_logged_in_user(
        client,
        test_user_payload,
    )

    response = await client.get(
        "/api/v1/auth/sessions",
        headers=bearer_headers(
            login_data["access_token"]
        ),
    )

    assert response.status_code == 200, response.text

    body = response.text.lower()

    assert "token_hash" not in body

    data = response.json()

    sessions = (
        data.get("sessions")
        if isinstance(data, dict)
        else data
    )

    if sessions is None:
        sessions = []

    for session in sessions:
        assert "token_hash" not in session
        assert "jti" not in session


# =========================================================
# REFRESH TOKENS MUST NOT BE STORED PLAINTEXT
# =========================================================


@pytest.mark.asyncio
async def test_refresh_token_is_not_stored_plaintext(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    login_data = await create_logged_in_user(
        client,
        test_user_payload,
    )

    refresh_token = login_data["refresh_token"]

    result = await db_session.execute(
        select(RefreshSession)
    )

    sessions = list(
        result.scalars().all()
    )

    assert sessions

    stored_hashes = [
        session.token_hash
        for session in sessions
    ]

    assert refresh_token not in stored_hashes

    for stored_hash in stored_hashes:
        assert stored_hash
        assert stored_hash != refresh_token


# =========================================================
# EMAIL VERIFICATION OTP MUST NOT BE STORED PLAINTEXT
# =========================================================


@pytest.mark.asyncio
async def test_email_verification_otp_is_not_stored_plaintext(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    response = await signup_user(
        client,
        test_user_payload,
    )

    assert response.status_code == 201, response.text

    result = await db_session.execute(
        select(EmailVerificationChallenge)
    )

    challenges = list(
        result.scalars().all()
    )

    assert challenges

    for challenge in challenges:
        assert challenge.otp_hash
        assert challenge.otp_hash != "123456"


# =========================================================
# PASSWORD RESET OTP MUST NOT BE STORED PLAINTEXT
# =========================================================


@pytest.mark.asyncio
async def test_password_reset_otp_is_not_stored_plaintext(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    await create_verified_user(
        client,
        test_user_payload,
    )

    response = await request_password_reset(
        client,
        email=test_user_payload["email"],
    )

    assert response.status_code == 200, response.text

    result = await db_session.execute(
        select(PasswordResetChallenge)
    )

    challenges = list(
        result.scalars().all()
    )

    assert challenges

    for challenge in challenges:
        assert challenge.otp_hash
        assert challenge.otp_hash != "123456"


# =========================================================
# RESET AUTHORIZATION TOKEN MUST NOT BE STORED PLAINTEXT
# =========================================================


@pytest.mark.asyncio
async def test_reset_authorization_token_is_not_stored_plaintext(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    await create_verified_user(
        client,
        test_user_payload,
    )

    forgot_response = await request_password_reset(
        client,
        email=test_user_payload["email"],
    )

    assert forgot_response.status_code == 200, forgot_response.text

    verify_response = await verify_reset_otp(
        client,
        email=test_user_payload["email"],
    )

    assert verify_response.status_code == 200, verify_response.text

    data = verify_response.json()

    reset_token = (
        data.get("reset_token")
        or data.get("token")
    )

    assert reset_token

    result = await db_session.execute(
        select(PasswordResetChallenge)
    )

    challenges = list(
        result.scalars().all()
    )

    assert challenges

    active_token_hashes = [
        challenge.reset_token_hash
        for challenge in challenges
        if challenge.reset_token_hash
    ]

    assert active_token_hashes

    assert reset_token not in active_token_hashes

    for token_hash in active_token_hashes:
        assert token_hash != reset_token


# =========================================================
# RESET AUTHORIZATION ROTATION
# =========================================================


@pytest.mark.asyncio
async def test_reverified_reset_otp_does_not_leave_old_token_valid(
    client: AsyncClient,
    test_user_payload,
):
    await create_verified_user(
        client,
        test_user_payload,
    )

    forgot_response = await request_password_reset(
        client,
        email=test_user_payload["email"],
    )

    assert forgot_response.status_code == 200, forgot_response.text

    first_verify = await verify_reset_otp(
        client,
        email=test_user_payload["email"],
    )

    assert first_verify.status_code == 200, first_verify.text

    first_data = first_verify.json()

    first_token = (
        first_data.get("reset_token")
        or first_data.get("token")
    )

    assert first_token

    second_verify = await verify_reset_otp(
        client,
        email=test_user_payload["email"],
    )

    assert second_verify.status_code == 200, second_verify.text

    second_data = second_verify.json()

    second_token = (
        second_data.get("reset_token")
        or second_data.get("token")
    )

    assert second_token
    assert second_token != first_token

    old_token_response = await client.post(
        "/api/v1/auth/reset-password",
        json={
            "reset_token": first_token,
            "new_password": "SecurityReset123!",
            "confirm_password": "SecurityReset123!",
        },
    )

    assert old_token_response.status_code in {
        400,
        401,
        403,
        409,
        422,
    }, old_token_response.text


# =========================================================
# REFRESH TOKEN ROTATION / REUSE DEFENSE
# =========================================================


@pytest.mark.asyncio
async def test_old_refresh_token_reuse_is_rejected_after_rotation(
    client: AsyncClient,
    test_user_payload,
):
    login_data = await create_logged_in_user(
        client,
        test_user_payload,
    )

    old_refresh_token = login_data["refresh_token"]

    first_refresh = await client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": old_refresh_token,
        },
    )

    assert first_refresh.status_code == 200, first_refresh.text

    reuse_response = await client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": old_refresh_token,
        },
    )

    assert reuse_response.status_code in {
        400,
        401,
        403,
    }, reuse_response.text


# =========================================================
# PASSWORD RESET MUST REVOKE EXISTING SESSIONS
# =========================================================


@pytest.mark.asyncio
async def test_password_reset_revokes_existing_refresh_session(
    client: AsyncClient,
    test_user_payload,
):
    login_data = await create_logged_in_user(
        client,
        test_user_payload,
    )

    existing_refresh_token = login_data["refresh_token"]

    forgot_response = await request_password_reset(
        client,
        email=test_user_payload["email"],
    )

    assert forgot_response.status_code == 200, forgot_response.text

    verify_response = await verify_reset_otp(
        client,
        email=test_user_payload["email"],
    )

    assert verify_response.status_code == 200, verify_response.text

    verify_data = verify_response.json()

    reset_token = (
        verify_data.get("reset_token")
        or verify_data.get("token")
    )

    assert reset_token

    new_password = "SecurityReset123!"

    reset_response = await client.post(
        "/api/v1/auth/reset-password",
        json={
            "reset_token": reset_token,
            "new_password": new_password,
            "confirm_password": new_password,
        },
    )

    assert reset_response.status_code == 200, reset_response.text

    old_session_response = await client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": existing_refresh_token,
        },
    )

    assert old_session_response.status_code in {
        400,
        401,
        403,
    }, old_session_response.text


# =========================================================
# PASSWORD RESET AUTHORIZATION MUST BE SINGLE USE
# =========================================================


@pytest.mark.asyncio
async def test_consumed_reset_token_cannot_be_reused(
    client: AsyncClient,
    test_user_payload,
):
    await create_verified_user(
        client,
        test_user_payload,
    )

    forgot_response = await request_password_reset(
        client,
        email=test_user_payload["email"],
    )

    assert forgot_response.status_code == 200, forgot_response.text

    verify_response = await verify_reset_otp(
        client,
        email=test_user_payload["email"],
    )

    assert verify_response.status_code == 200, verify_response.text

    verify_data = verify_response.json()

    reset_token = (
        verify_data.get("reset_token")
        or verify_data.get("token")
    )

    assert reset_token

    new_password = "SecurityReset123!"

    first_reset = await client.post(
        "/api/v1/auth/reset-password",
        json={
            "reset_token": reset_token,
            "new_password": new_password,
            "confirm_password": new_password,
        },
    )

    assert first_reset.status_code == 200, first_reset.text

    second_reset = await client.post(
        "/api/v1/auth/reset-password",
        json={
            "reset_token": reset_token,
            "new_password": "AnotherSecurity123!",
            "confirm_password": "AnotherSecurity123!",
        },
    )

    assert second_reset.status_code in {
        400,
        401,
        403,
        409,
        422,
    }, second_reset.text


# =========================================================
# FORGOT PASSWORD ANTI-ENUMERATION
# =========================================================


@pytest.mark.asyncio
async def test_forgot_password_unknown_email_does_not_enumerate_account(
    client: AsyncClient,
):
    response = await request_password_reset(
        client,
        email="definitely.missing.user@example.com",
    )

    assert response.status_code == 200, response.text

    body = response.text.lower()

    assert "user not found" not in body
    assert "account not found" not in body
    assert "email not found" not in body
    assert "does not exist" not in body
    assert "unknown user" not in body


# =========================================================
# CROSS-USER SESSION ISOLATION
# =========================================================


@pytest.mark.asyncio
async def test_user_cannot_revoke_another_users_session(
    client: AsyncClient,
    db_session,
    test_user_payload,
    second_test_user_payload,
):
    first_login = await create_logged_in_user(
        client,
        test_user_payload,
    )

    second_login = await create_logged_in_user(
        client,
        second_test_user_payload,
    )

    first_access_token = first_login["access_token"]
    second_access_token = second_login["access_token"]

    second_me = await client.get(
        "/api/v1/auth/me",
        headers=bearer_headers(
            second_access_token
        ),
    )

    assert second_me.status_code == 200, second_me.text

    second_user_data = extract_user(
        second_me.json()
    )

    second_user_id = UUID(
        str(second_user_data["id"])
    )

    result = await db_session.execute(
        select(RefreshSession).where(
            RefreshSession.user_id == second_user_id,
            RefreshSession.revoked_at.is_(None),
        )
    )

    second_sessions = list(
        result.scalars().all()
    )

    assert second_sessions

    # Save the scalar before rollback/expiration boundaries.
    second_session_id = second_sessions[0].id

    response = await client.delete(
        f"/api/v1/auth/sessions/{second_session_id}",
        headers=bearer_headers(
            first_access_token
        ),
    )

    assert response.status_code in {
        403,
        404,
    }, response.text

    # The second user's refresh session must still function.
    refresh_response = await client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": second_login[
                "refresh_token"
            ],
        },
    )

    assert refresh_response.status_code == 200, refresh_response.text


# =========================================================
# LOGOUT-ALL USER ISOLATION
# =========================================================


@pytest.mark.asyncio
async def test_logout_all_does_not_revoke_another_users_session(
    client: AsyncClient,
    test_user_payload,
    second_test_user_payload,
):
    first_login = await create_logged_in_user(
        client,
        test_user_payload,
    )

    second_login = await create_logged_in_user(
        client,
        second_test_user_payload,
    )

    logout_all_response = await client.post(
        "/api/v1/auth/logout-all",
        headers=bearer_headers(
            first_login["access_token"]
        ),
    )

    assert logout_all_response.status_code == 200, logout_all_response.text

    second_refresh_response = await client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": second_login[
                "refresh_token"
            ],
        },
    )

    assert second_refresh_response.status_code == 200, (
        second_refresh_response.text
    )


# =========================================================
# ACCOUNT STATUS SECURITY
# =========================================================


@pytest.mark.asyncio
async def test_unverified_account_cannot_login(
    client: AsyncClient,
    test_user_payload,
):
    signup_response = await signup_user(
        client,
        test_user_payload,
    )

    assert signup_response.status_code == 201, signup_response.text

    login_response = await login_user(
        client,
        identifier=test_user_payload["email"],
        password=test_user_payload["password"],
    )

    assert login_response.status_code == 401, login_response.text

    data = login_response.json()

    body = str(data)

    assert "EMAIL_NOT_VERIFIED" in body


# =========================================================
# API ERRORS MUST NOT LEAK INTERNAL INFRASTRUCTURE
# =========================================================


@pytest.mark.asyncio
async def test_invalid_auth_does_not_expose_internal_infrastructure(
    client: AsyncClient,
):
    response = await login_user(
        client,
        identifier="missing.user@example.com",
        password="WrongPassword123!",
    )

    body = response.text.lower()

    forbidden_fragments = (
        "traceback",
        "asyncpg",
        "sqlalchemy",
        "redis://",
        "postgresql://",
        "localhost:5434",
        "localhost:6381",
        "database_url",
        "control_database_url",
        "jwt_secret",
        "secret_key",
        "smtp_password",
    )

    for fragment in forbidden_fragments:
        assert fragment not in body


# =========================================================
# AUTH RESPONSES MUST NOT EXPOSE OTP OR RESET HASH INTERNALS
# =========================================================


@pytest.mark.asyncio
async def test_signup_response_does_not_expose_verification_secret_fields(
    client: AsyncClient,
    test_user_payload,
):
    response = await signup_user(
        client,
        test_user_payload,
    )

    assert response.status_code == 201, response.text

    body = response.text.lower()

    assert "otp_hash" not in body
    assert "reset_token_hash" not in body


@pytest.mark.asyncio
async def test_forgot_password_response_does_not_expose_reset_secret_fields(
    client: AsyncClient,
    test_user_payload,
):
    await create_verified_user(
        client,
        test_user_payload,
    )

    response = await request_password_reset(
        client,
        email=test_user_payload["email"],
    )

    assert response.status_code == 200, response.text

    body = response.text.lower()

    assert "otp_hash" not in body
    assert "reset_token_hash" not in body


# =========================================================
# USER IDS / SESSION IDS SHOULD BE VALID UUIDS
# =========================================================


@pytest.mark.asyncio
async def test_authenticated_user_id_is_uuid(
    client: AsyncClient,
    test_user_payload,
):
    login_data = await create_logged_in_user(
        client,
        test_user_payload,
    )

    response = await client.get(
        "/api/v1/auth/me",
        headers=bearer_headers(
            login_data["access_token"]
        ),
    )

    assert response.status_code == 200, response.text

    user = extract_user(
        response.json()
    )

    user_id = UUID(
        str(user["id"])
    )

    assert isinstance(user_id, UUID)


# =========================================================
# DATABASE USER PASSWORD MUST REMAIN HASHED
# =========================================================


@pytest.mark.asyncio
async def test_tampered_access_token_is_rejected(
    client: AsyncClient,
    test_user_payload,
):
    login_data = await create_logged_in_user(
        client,
        test_user_payload,
    )

    access_token = login_data["access_token"]

    parts = access_token.split(".")

    assert len(parts) == 3

    header_segment, payload_segment, signature_segment = parts

    assert payload_segment

    tamper_index = len(payload_segment) // 2
    original_character = payload_segment[tamper_index]

    replacement_character = (
        "a"
        if original_character != "a"
        else "b"
    )

    tampered_payload_segment = (
        payload_segment[:tamper_index]
        + replacement_character
        + payload_segment[tamper_index + 1 :]
    )

    tampered_token = ".".join(
        (
            header_segment,
            tampered_payload_segment,
            signature_segment,
        )
    )

    assert tampered_token != access_token

    response = await client.get(
        "/api/v1/auth/me",
        headers=bearer_headers(
            tampered_token
        ),
    )

    assert response.status_code in {
        401,
        403,
    }, response.text