from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.modules.auth.models import (
    PasswordResetChallenge,
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
    password: str | None = None,
) -> dict:
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "identifier": payload["email"],
            "password": (
                password
                if password is not None
                else payload["password"]
            ),
            "remember_me": False,
        },
    )

    assert response.status_code == 200, response.text

    return response.json()


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


async def get_password_reset_challenges(
    db_session,
    user_id,
) -> list[PasswordResetChallenge]:
    result = await db_session.execute(
        select(PasswordResetChallenge)
        .where(
            PasswordResetChallenge.user_id == user_id
        )
        .order_by(
            PasswordResetChallenge.created_at.desc()
        )
    )

    return list(
        result.scalars().all()
    )


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


def extract_reset_token(
    payload: dict,
) -> str:
    """
    Support common verify-reset-otp response shapes.

    Examples:

        {
            "reset_token": "..."
        }

    or:

        {
            "data": {
                "reset_token": "..."
            }
        }

    or:

        {
            "authorization": {
                "reset_token": "..."
            }
        }
    """

    direct = payload.get("reset_token")

    if isinstance(direct, str) and direct:
        return direct

    data = payload.get("data")

    if isinstance(data, dict):
        token = data.get("reset_token")

        if isinstance(token, str) and token:
            return token

    authorization = payload.get("authorization")

    if isinstance(authorization, dict):
        token = authorization.get(
            "reset_token"
        )

        if isinstance(token, str) and token:
            return token

    raise AssertionError(
        f"reset_token not found in response: {payload}"
    )


async def request_password_reset(
    client: AsyncClient,
    email: str,
) -> None:
    response = await client.post(
        "/api/v1/auth/forgot-password",
        json={
            "email": email,
        },
    )

    assert response.status_code == 200, response.text


async def verify_password_reset_otp(
    client: AsyncClient,
    email: str,
) -> str:
    response = await client.post(
        "/api/v1/auth/verify-reset-otp",
        json={
            "email": email,
            "otp": "123456",
        },
    )

    assert response.status_code == 200, response.text

    return extract_reset_token(
        response.json()
    )


async def reset_password(
    client: AsyncClient,
    *,
    reset_token: str,
    new_password: str,
) -> None:
    response = await client.post(
        "/api/v1/auth/reset-password",
        json={
            "reset_token": reset_token,
            "new_password": new_password,
            "confirm_password": new_password,
        },
    )

    assert response.status_code == 200, response.text


# =========================================================
# FORGOT PASSWORD — VERIFIED USER
# =========================================================


@pytest.mark.asyncio
async def test_forgot_password_verified_user_succeeds(
    client: AsyncClient,
    test_user_payload,
):
    await signup_and_verify(
        client,
        test_user_payload,
    )

    response = await client.post(
        "/api/v1/auth/forgot-password",
        json={
            "email": test_user_payload["email"],
        },
    )

    assert response.status_code == 200, response.text


# =========================================================
# FORGOT PASSWORD — UNKNOWN USER SAFE RESPONSE
# =========================================================


@pytest.mark.asyncio
async def test_forgot_password_unknown_user_safe_response(
    client: AsyncClient,
):
    response = await client.post(
        "/api/v1/auth/forgot-password",
        json={
            "email": "missing.user@example.com",
        },
    )

    # Anti-enumeration behavior:
    # unknown accounts should receive the same general success-style
    # response instead of revealing whether the user exists.
    assert response.status_code == 200, response.text


# =========================================================
# INVALID EMAIL FORMAT
# =========================================================


@pytest.mark.asyncio
async def test_forgot_password_invalid_email_rejected(
    client: AsyncClient,
):
    response = await client.post(
        "/api/v1/auth/forgot-password",
        json={
            "email": "not-an-email",
        },
    )

    assert response.status_code == 422, response.text


# =========================================================
# RESET CHALLENGE CREATED
# =========================================================


@pytest.mark.asyncio
async def test_forgot_password_creates_reset_challenge(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    await signup_and_verify(
        client,
        test_user_payload,
    )

    await request_password_reset(
        client,
        test_user_payload["email"],
    )

    await db_session.rollback()

    user = await get_user_by_email(
        db_session,
        test_user_payload["email"],
    )

    user_id = user.id

    challenges = await get_password_reset_challenges(
        db_session,
        user_id,
    )

    assert len(challenges) == 1

    challenge = challenges[0]

    assert challenge.otp_hash
    assert challenge.expires_at is not None
    assert challenge.consumed_at is None
    assert challenge.invalidated_at is None


# =========================================================
# OTP NEVER STORED PLAINTEXT
# =========================================================


@pytest.mark.asyncio
async def test_password_reset_otp_not_stored_plaintext(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    await signup_and_verify(
        client,
        test_user_payload,
    )

    await request_password_reset(
        client,
        test_user_payload["email"],
    )

    await db_session.rollback()

    user = await get_user_by_email(
        db_session,
        test_user_payload["email"],
    )

    user_id = user.id

    challenges = await get_password_reset_challenges(
        db_session,
        user_id,
    )

    assert len(challenges) == 1

    challenge = challenges[0]

    assert challenge.otp_hash
    assert challenge.otp_hash != "123456"
    assert "123456" not in challenge.otp_hash


# =========================================================
# VERIFY VALID RESET OTP
# =========================================================


@pytest.mark.asyncio
async def test_verify_reset_otp_success(
    client: AsyncClient,
    test_user_payload,
):
    await signup_and_verify(
        client,
        test_user_payload,
    )

    await request_password_reset(
        client,
        test_user_payload["email"],
    )

    response = await client.post(
        "/api/v1/auth/verify-reset-otp",
        json={
            "email": test_user_payload["email"],
            "otp": "123456",
        },
    )

    assert response.status_code == 200, response.text

    reset_token = extract_reset_token(
        response.json()
    )

    assert reset_token


# =========================================================
# WRONG RESET OTP
# =========================================================


@pytest.mark.asyncio
async def test_verify_reset_otp_wrong_code_rejected(
    client: AsyncClient,
    test_user_payload,
):
    await signup_and_verify(
        client,
        test_user_payload,
    )

    await request_password_reset(
        client,
        test_user_payload["email"],
    )

    response = await client.post(
        "/api/v1/auth/verify-reset-otp",
        json={
            "email": test_user_payload["email"],
            "otp": "654321",
        },
    )

    assert response.status_code in {
        400,
        401,
        422,
    }, response.text


# =========================================================
# RESET TOKEN STORED HASHED
# =========================================================


@pytest.mark.asyncio
async def test_reset_authorization_token_not_stored_plaintext(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    await signup_and_verify(
        client,
        test_user_payload,
    )

    await request_password_reset(
        client,
        test_user_payload["email"],
    )

    reset_token = await verify_password_reset_otp(
        client,
        test_user_payload["email"],
    )

    await db_session.rollback()

    user = await get_user_by_email(
        db_session,
        test_user_payload["email"],
    )

    user_id = user.id

    challenges = await get_password_reset_challenges(
        db_session,
        user_id,
    )

    assert len(challenges) == 1

    challenge = challenges[0]

    assert challenge.reset_token_hash
    assert challenge.reset_token_hash != reset_token
    assert reset_token not in challenge.reset_token_hash


# =========================================================
# RESET TOKEN EXPIRY EXISTS
# =========================================================


@pytest.mark.asyncio
async def test_reset_token_has_expiration(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    await signup_and_verify(
        client,
        test_user_payload,
    )

    await request_password_reset(
        client,
        test_user_payload["email"],
    )

    await verify_password_reset_otp(
        client,
        test_user_payload["email"],
    )

    await db_session.rollback()

    user = await get_user_by_email(
        db_session,
        test_user_payload["email"],
    )

    user_id = user.id

    challenges = await get_password_reset_challenges(
        db_session,
        user_id,
    )

    challenge = challenges[0]

    assert challenge.reset_token_hash
    assert challenge.reset_token_expires_at is not None


# =========================================================
# COMPLETE PASSWORD RESET
# =========================================================


@pytest.mark.asyncio
async def test_reset_password_success(
    client: AsyncClient,
    test_user_payload,
):
    await signup_and_verify(
        client,
        test_user_payload,
    )

    await request_password_reset(
        client,
        test_user_payload["email"],
    )

    reset_token = await verify_password_reset_otp(
        client,
        test_user_payload["email"],
    )

    new_password = "NewStrongPassword456!"

    response = await client.post(
        "/api/v1/auth/reset-password",
        json={
            "reset_token": reset_token,
            "new_password": new_password,
            "confirm_password": new_password,
        },
    )

    assert response.status_code == 200, response.text


# =========================================================
# OLD PASSWORD STOPS WORKING
# =========================================================


@pytest.mark.asyncio
async def test_old_password_rejected_after_reset(
    client: AsyncClient,
    test_user_payload,
):
    await signup_and_verify(
        client,
        test_user_payload,
    )

    await request_password_reset(
        client,
        test_user_payload["email"],
    )

    reset_token = await verify_password_reset_otp(
        client,
        test_user_payload["email"],
    )

    new_password = "NewStrongPassword456!"

    await reset_password(
        client,
        reset_token=reset_token,
        new_password=new_password,
    )

    old_login = await client.post(
        "/api/v1/auth/login",
        json={
            "identifier": test_user_payload["email"],
            "password": test_user_payload["password"],
            "remember_me": False,
        },
    )

    assert old_login.status_code == 401, old_login.text


# =========================================================
# NEW PASSWORD WORKS
# =========================================================


@pytest.mark.asyncio
async def test_new_password_can_login_after_reset(
    client: AsyncClient,
    test_user_payload,
):
    await signup_and_verify(
        client,
        test_user_payload,
    )

    await request_password_reset(
        client,
        test_user_payload["email"],
    )

    reset_token = await verify_password_reset_otp(
        client,
        test_user_payload["email"],
    )

    new_password = "NewStrongPassword456!"

    await reset_password(
        client,
        reset_token=reset_token,
        new_password=new_password,
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "identifier": test_user_payload["email"],
            "password": new_password,
            "remember_me": False,
        },
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["access_token"]
    assert data["refresh_token"]


# =========================================================
# PASSWORD HASH CHANGED
# =========================================================


@pytest.mark.asyncio
async def test_password_hash_changes_after_reset(
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

    old_hash = user_before.password_hash

    assert old_hash

    await db_session.rollback()

    await request_password_reset(
        client,
        test_user_payload["email"],
    )

    reset_token = await verify_password_reset_otp(
        client,
        test_user_payload["email"],
    )

    new_password = "NewStrongPassword456!"

    await reset_password(
        client,
        reset_token=reset_token,
        new_password=new_password,
    )

    await db_session.rollback()

    user_after = await get_user_by_email(
        db_session,
        test_user_payload["email"],
    )

    assert user_after.password_hash
    assert user_after.password_hash != old_hash
    assert user_after.password_hash != new_password
    assert new_password not in user_after.password_hash


# =========================================================
# RESET TOKEN CANNOT BE REUSED
# =========================================================


@pytest.mark.asyncio
async def test_reset_token_cannot_be_reused(
    client: AsyncClient,
    test_user_payload,
):
    await signup_and_verify(
        client,
        test_user_payload,
    )

    await request_password_reset(
        client,
        test_user_payload["email"],
    )

    reset_token = await verify_password_reset_otp(
        client,
        test_user_payload["email"],
    )

    first_password = "NewStrongPassword456!"

    first_response = await client.post(
        "/api/v1/auth/reset-password",
        json={
            "reset_token": reset_token,
            "new_password": first_password,
            "confirm_password": first_password,
        },
    )

    assert first_response.status_code == 200, first_response.text

    second_password = "AnotherStrongPassword789!"

    second_response = await client.post(
        "/api/v1/auth/reset-password",
        json={
            "reset_token": reset_token,
            "new_password": second_password,
            "confirm_password": second_password,
        },
    )

    assert second_response.status_code in {
        400,
        401,
        409,
        422,
    }, second_response.text


# =========================================================
# RESET CHALLENGE CONSUMED
# =========================================================


@pytest.mark.asyncio
async def test_password_reset_challenge_consumed_after_success(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    await signup_and_verify(
        client,
        test_user_payload,
    )

    await request_password_reset(
        client,
        test_user_payload["email"],
    )

    reset_token = await verify_password_reset_otp(
        client,
        test_user_payload["email"],
    )

    await reset_password(
        client,
        reset_token=reset_token,
        new_password="NewStrongPassword456!",
    )

    await db_session.rollback()

    user = await get_user_by_email(
        db_session,
        test_user_payload["email"],
    )

    user_id = user.id

    challenges = await get_password_reset_challenges(
        db_session,
        user_id,
    )

    assert len(challenges) == 1

    challenge = challenges[0]

    assert challenge.consumed_at is not None


# =========================================================
# PASSWORD CHANGED TIMESTAMP
# =========================================================


@pytest.mark.asyncio
async def test_password_changed_at_updated_after_reset(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    await signup_and_verify(
        client,
        test_user_payload,
    )

    await request_password_reset(
        client,
        test_user_payload["email"],
    )

    reset_token = await verify_password_reset_otp(
        client,
        test_user_payload["email"],
    )

    await reset_password(
        client,
        reset_token=reset_token,
        new_password="NewStrongPassword456!",
    )

    await db_session.rollback()

    user = await get_user_by_email(
        db_session,
        test_user_payload["email"],
    )

    assert user.password_changed_at is not None


# =========================================================
# EXISTING LOGIN SESSION IS REVOKED
# =========================================================


@pytest.mark.asyncio
async def test_password_reset_revokes_existing_sessions(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    await signup_and_verify(
        client,
        test_user_payload,
    )

    login_data = await login_user(
        client,
        test_user_payload,
    )

    old_refresh_token = login_data["refresh_token"]

    await request_password_reset(
        client,
        test_user_payload["email"],
    )

    reset_token = await verify_password_reset_otp(
        client,
        test_user_payload["email"],
    )

    await reset_password(
        client,
        reset_token=reset_token,
        new_password="NewStrongPassword456!",
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

    assert len(sessions) >= 1

    assert all(
        session.revoked_at is not None
        for session in sessions
    )

    refresh_response = await client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": old_refresh_token,
        },
    )

    assert refresh_response.status_code in {
        400,
        401,
        403,
        409,
    }, refresh_response.text


# =========================================================
# MULTIPLE EXISTING SESSIONS REVOKED
# =========================================================


@pytest.mark.asyncio
async def test_password_reset_revokes_all_existing_sessions(
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

    assert first_login["refresh_token"]
    assert second_login["refresh_token"]

    await request_password_reset(
        client,
        test_user_payload["email"],
    )

    reset_token = await verify_password_reset_otp(
        client,
        test_user_payload["email"],
    )

    await reset_password(
        client,
        reset_token=reset_token,
        new_password="NewStrongPassword456!",
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

    assert all(
        session.revoked_at is not None
        for session in sessions
    )


# =========================================================
# NEW SESSION CAN BE CREATED AFTER RESET
# =========================================================


@pytest.mark.asyncio
async def test_user_can_create_new_session_after_password_reset(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    await signup_and_verify(
        client,
        test_user_payload,
    )

    old_login = await login_user(
        client,
        test_user_payload,
    )

    await request_password_reset(
        client,
        test_user_payload["email"],
    )

    reset_token = await verify_password_reset_otp(
        client,
        test_user_payload["email"],
    )

    new_password = "NewStrongPassword456!"

    await reset_password(
        client,
        reset_token=reset_token,
        new_password=new_password,
    )

    new_login = await login_user(
        client,
        test_user_payload,
        password=new_password,
    )

    assert new_login["refresh_token"]
    assert (
        new_login["refresh_token"]
        != old_login["refresh_token"]
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

    active_sessions = [
        session
        for session in sessions
        if session.revoked_at is None
    ]

    assert len(active_sessions) == 1


# =========================================================
# PASSWORD MISMATCH
# =========================================================


@pytest.mark.asyncio
async def test_reset_password_mismatch_rejected(
    client: AsyncClient,
    test_user_payload,
):
    await signup_and_verify(
        client,
        test_user_payload,
    )

    await request_password_reset(
        client,
        test_user_payload["email"],
    )

    reset_token = await verify_password_reset_otp(
        client,
        test_user_payload["email"],
    )

    response = await client.post(
        "/api/v1/auth/reset-password",
        json={
            "reset_token": reset_token,
            "new_password": "NewStrongPassword456!",
            "confirm_password": "DifferentPassword789!",
        },
    )

    assert response.status_code == 422, response.text


# =========================================================
# WEAK NEW PASSWORD
# =========================================================


@pytest.mark.asyncio
async def test_reset_password_weak_password_rejected(
    client: AsyncClient,
    test_user_payload,
):
    await signup_and_verify(
        client,
        test_user_payload,
    )

    await request_password_reset(
        client,
        test_user_payload["email"],
    )

    reset_token = await verify_password_reset_otp(
        client,
        test_user_payload["email"],
    )

    response = await client.post(
        "/api/v1/auth/reset-password",
        json={
            "reset_token": reset_token,
            "new_password": "weak",
            "confirm_password": "weak",
        },
    )

    assert response.status_code in {
        400,
        422,
    }, response.text


# =========================================================
# INVALID RESET TOKEN
# =========================================================


@pytest.mark.asyncio
async def test_invalid_reset_token_rejected(
    client: AsyncClient,
):
    response = await client.post(
        "/api/v1/auth/reset-password",
        json={
            "reset_token": "invalid-reset-token",
            "new_password": "NewStrongPassword456!",
            "confirm_password": "NewStrongPassword456!",
        },
    )

    assert response.status_code in {
        400,
        401,
        404,
        422,
    }, response.text


# =========================================================
# MISSING RESET TOKEN
# =========================================================


@pytest.mark.asyncio
async def test_missing_reset_token_rejected(
    client: AsyncClient,
):
    response = await client.post(
        "/api/v1/auth/reset-password",
        json={
            "new_password": "NewStrongPassword456!",
            "confirm_password": "NewStrongPassword456!",
        },
    )

    assert response.status_code == 422, response.text


# =========================================================
# REVERIFYING OTP ROTATES RESET AUTHORIZATION
# =========================================================


@pytest.mark.asyncio
async def test_reverifying_reset_otp_rotates_reset_authorization(
    client: AsyncClient,
    test_user_payload,
):
    """
    Re-verifying the same still-valid password-reset OTP is allowed
    by the current API, but it must rotate the reset authorization
    token so that only the latest reset token remains usable.
    """

    await signup_and_verify(
        client,
        test_user_payload,
    )

    await request_password_reset(
        client,
        test_user_payload["email"],
    )

    first_response = await client.post(
        "/api/v1/auth/verify-reset-otp",
        json={
            "email": test_user_payload["email"],
            "otp": "123456",
        },
    )

    assert first_response.status_code == 200, first_response.text

    first_reset_token = extract_reset_token(
        first_response.json()
    )

    assert first_reset_token

    second_response = await client.post(
        "/api/v1/auth/verify-reset-otp",
        json={
            "email": test_user_payload["email"],
            "otp": "123456",
        },
    )

    assert second_response.status_code == 200, second_response.text

    second_reset_token = extract_reset_token(
        second_response.json()
    )

    assert second_reset_token
    assert second_reset_token != first_reset_token

    old_token_response = await client.post(
        "/api/v1/auth/reset-password",
        json={
            "reset_token": first_reset_token,
            "new_password": "OldTokenMustFail456!",
            "confirm_password": "OldTokenMustFail456!",
        },
    )

    assert old_token_response.status_code in {
        400,
        401,
        404,
        409,
        422,
    }, old_token_response.text

    new_token_response = await client.post(
        "/api/v1/auth/reset-password",
        json={
            "reset_token": second_reset_token,
            "new_password": "NewStrongPassword456!",
            "confirm_password": "NewStrongPassword456!",
        },
    )

    assert new_token_response.status_code == 200, new_token_response.text


# =========================================================
# PASSWORD RESET DOES NOT UNVERIFY EMAIL
# =========================================================


@pytest.mark.asyncio
async def test_password_reset_keeps_email_verified(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    await signup_and_verify(
        client,
        test_user_payload,
    )

    await request_password_reset(
        client,
        test_user_payload["email"],
    )

    reset_token = await verify_password_reset_otp(
        client,
        test_user_payload["email"],
    )

    await reset_password(
        client,
        reset_token=reset_token,
        new_password="NewStrongPassword456!",
    )

    await db_session.rollback()

    user = await get_user_by_email(
        db_session,
        test_user_payload["email"],
    )

    assert user.is_email_verified is True
    assert user.email_verified_at is not None


# =========================================================
# PASSWORD RESET DOES NOT DISABLE ACCOUNT
# =========================================================


@pytest.mark.asyncio
async def test_password_reset_keeps_account_active(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    await signup_and_verify(
        client,
        test_user_payload,
    )

    await request_password_reset(
        client,
        test_user_payload["email"],
    )

    reset_token = await verify_password_reset_otp(
        client,
        test_user_payload["email"],
    )

    await reset_password(
        client,
        reset_token=reset_token,
        new_password="NewStrongPassword456!",
    )

    await db_session.rollback()

    user = await get_user_by_email(
        db_session,
        test_user_payload["email"],
    )

    assert user.is_active is True
    assert user.is_locked is False