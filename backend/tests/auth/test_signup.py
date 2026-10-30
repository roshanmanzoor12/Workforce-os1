from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.modules.auth.models import (
    EmailVerificationChallenge,
    User,
)


# =========================================================
# SUCCESSFUL SIGNUP
# =========================================================


@pytest.mark.asyncio
async def test_signup_success(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    response = await client.post(
        "/api/v1/auth/signup",
        json=test_user_payload,
    )

    assert response.status_code == 201, response.text

    data = response.json()

    assert data["user"]["email"] == test_user_payload["email"]
    assert data["user"]["username"] == test_user_payload["username"]
    assert data["user"]["first_name"] == test_user_payload["first_name"]
    assert data["user"]["last_name"] == test_user_payload["last_name"]

    assert data["user"]["is_email_verified"] is False
    assert data["user"]["is_active"] is True
    assert data["user"]["is_locked"] is False

    result = await db_session.execute(
        select(User).where(
            User.email == test_user_payload["email"]
        )
    )

    user = result.scalar_one_or_none()

    assert user is not None

    assert user.email == test_user_payload["email"]
    assert user.username == test_user_payload["username"]

    assert user.password_hash is not None
    assert user.password_hash != test_user_payload["password"]


# =========================================================
# VERIFICATION CHALLENGE CREATED
# =========================================================


@pytest.mark.asyncio
async def test_signup_creates_verification_challenge(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    response = await client.post(
        "/api/v1/auth/signup",
        json=test_user_payload,
    )

    assert response.status_code == 201, response.text

    user_result = await db_session.execute(
        select(User).where(
            User.email == test_user_payload["email"]
        )
    )

    user = user_result.scalar_one()

    challenge_result = await db_session.execute(
        select(EmailVerificationChallenge)
        .where(
            EmailVerificationChallenge.user_id == user.id
        )
        .order_by(
            EmailVerificationChallenge.created_at.desc()
        )
    )

    challenge = challenge_result.scalars().first()

    assert challenge is not None

    assert challenge.sent_to_email == test_user_payload["email"]

    assert challenge.attempt_count == 0

    assert challenge.max_attempts >= 1

    assert challenge.expires_at is not None

    assert challenge.verified_at is None
    assert challenge.consumed_at is None
    assert challenge.invalidated_at is None


# =========================================================
# OTP MUST NOT BE STORED AS PLAINTEXT
# =========================================================


@pytest.mark.asyncio
async def test_signup_does_not_store_plaintext_otp(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    response = await client.post(
        "/api/v1/auth/signup",
        json=test_user_payload,
    )

    assert response.status_code == 201, response.text

    user_result = await db_session.execute(
        select(User).where(
            User.email == test_user_payload["email"]
        )
    )

    user = user_result.scalar_one()

    challenge_result = await db_session.execute(
        select(EmailVerificationChallenge)
        .where(
            EmailVerificationChallenge.user_id == user.id
        )
        .order_by(
            EmailVerificationChallenge.created_at.desc()
        )
    )

    challenge = challenge_result.scalars().first()

    assert challenge is not None

    assert challenge.otp_hash is not None

    # Tests use deterministic OTP 123456,
    # but database must contain only the HMAC/hash.
    assert challenge.otp_hash != "123456"

    assert "123456" not in challenge.otp_hash


# =========================================================
# DUPLICATE EMAIL
# =========================================================


@pytest.mark.asyncio
async def test_signup_duplicate_email_rejected(
    client: AsyncClient,
    test_user_payload,
):
    first_response = await client.post(
        "/api/v1/auth/signup",
        json=test_user_payload,
    )

    assert first_response.status_code == 201, first_response.text

    duplicate_payload = {
        **test_user_payload,
        "username": "differentusername",
    }

    second_response = await client.post(
        "/api/v1/auth/signup",
        json=duplicate_payload,
    )

    assert second_response.status_code == 409, second_response.text

    data = second_response.json()

    assert "error" in data

    assert data["error"]["code"] in {
        "EMAIL_ALREADY_EXISTS",
        "CONFLICT",
    }


# =========================================================
# DUPLICATE USERNAME
# =========================================================


@pytest.mark.asyncio
async def test_signup_duplicate_username_rejected(
    client: AsyncClient,
    test_user_payload,
):
    first_response = await client.post(
        "/api/v1/auth/signup",
        json=test_user_payload,
    )

    assert first_response.status_code == 201, first_response.text

    duplicate_payload = {
        **test_user_payload,
        "email": "another.user@example.com",
    }

    second_response = await client.post(
        "/api/v1/auth/signup",
        json=duplicate_payload,
    )

    assert second_response.status_code == 409, second_response.text

    data = second_response.json()

    assert "error" in data

    assert data["error"]["code"] in {
        "USERNAME_ALREADY_EXISTS",
        "CONFLICT",
    }


# =========================================================
# PASSWORD CONFIRMATION
# =========================================================


@pytest.mark.asyncio
async def test_signup_password_confirmation_mismatch(
    client: AsyncClient,
    test_user_payload,
):
    payload = {
        **test_user_payload,
        "confirm_password": "DifferentPassword123!",
    }

    response = await client.post(
        "/api/v1/auth/signup",
        json=payload,
    )

    assert response.status_code in {
        400,
        422,
    }, response.text


# =========================================================
# INVALID EMAIL
# =========================================================


@pytest.mark.asyncio
async def test_signup_invalid_email_rejected(
    client: AsyncClient,
    test_user_payload,
):
    payload = {
        **test_user_payload,
        "email": "not-an-email",
    }

    response = await client.post(
        "/api/v1/auth/signup",
        json=payload,
    )

    assert response.status_code == 422, response.text

    data = response.json()

    assert "error" in data

    assert data["error"]["code"] == "VALIDATION_ERROR"


# =========================================================
# SHORT USERNAME
# =========================================================


@pytest.mark.asyncio
async def test_signup_short_username_rejected(
    client: AsyncClient,
    test_user_payload,
):
    payload = {
        **test_user_payload,
        "username": "ab",
    }

    response = await client.post(
        "/api/v1/auth/signup",
        json=payload,
    )

    assert response.status_code == 422, response.text


# =========================================================
# WEAK PASSWORD
# =========================================================


@pytest.mark.asyncio
async def test_signup_weak_password_rejected(
    client: AsyncClient,
    test_user_payload,
):
    payload = {
        **test_user_payload,
        "password": "123",
        "confirm_password": "123",
    }

    response = await client.post(
        "/api/v1/auth/signup",
        json=payload,
    )

    assert response.status_code in {
        400,
        422,
    }, response.text


# =========================================================
# EMAIL NORMALIZATION
# =========================================================


@pytest.mark.asyncio
async def test_signup_email_is_normalized(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    payload = {
        **test_user_payload,
        "email": "  TEST.AUTH@EXAMPLE.COM  ",
    }

    response = await client.post(
        "/api/v1/auth/signup",
        json=payload,
    )

    assert response.status_code == 201, response.text

    result = await db_session.execute(
        select(User).where(
            User.email == "test.auth@example.com"
        )
    )

    user = result.scalar_one_or_none()

    assert user is not None

    assert user.email == "test.auth@example.com"


# =========================================================
# USERNAME NORMALIZATION
# =========================================================


@pytest.mark.asyncio
async def test_signup_username_is_normalized(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    payload = {
        **test_user_payload,
        "username": "  TestAuthUser  ",
    }

    response = await client.post(
        "/api/v1/auth/signup",
        json=payload,
    )

    assert response.status_code == 201, response.text

    result = await db_session.execute(
        select(User).where(
            User.username == "testauthuser"
        )
    )

    user = result.scalar_one_or_none()

    assert user is not None

    assert user.username == "testauthuser"


# =========================================================
# ONLY ONE USER CREATED
# =========================================================


@pytest.mark.asyncio
async def test_signup_creates_only_one_user(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    response = await client.post(
        "/api/v1/auth/signup",
        json=test_user_payload,
    )

    assert response.status_code == 201, response.text

    result = await db_session.execute(
        select(User)
    )

    users = result.scalars().all()

    assert len(users) == 1


# =========================================================
# PASSWORD MUST NOT BE PLAINTEXT
# =========================================================


@pytest.mark.asyncio
async def test_signup_does_not_store_plaintext_password(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    response = await client.post(
        "/api/v1/auth/signup",
        json=test_user_payload,
    )

    assert response.status_code == 201, response.text

    result = await db_session.execute(
        select(User).where(
            User.email == test_user_payload["email"]
        )
    )

    user = result.scalar_one()

    assert user.password_hash is not None

    assert user.password_hash != test_user_payload["password"]

    assert test_user_payload["password"] not in user.password_hash


# =========================================================
# USER STARTS UNVERIFIED
# =========================================================


@pytest.mark.asyncio
async def test_signup_user_starts_unverified(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    response = await client.post(
        "/api/v1/auth/signup",
        json=test_user_payload,
    )

    assert response.status_code == 201, response.text

    result = await db_session.execute(
        select(User).where(
            User.email == test_user_payload["email"]
        )
    )

    user = result.scalar_one()

    assert user.is_email_verified is False

    assert user.email_verified_at is None


# =========================================================
# USER STARTS ACTIVE AND UNLOCKED
# =========================================================


@pytest.mark.asyncio
async def test_signup_user_starts_active_and_unlocked(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    response = await client.post(
        "/api/v1/auth/signup",
        json=test_user_payload,
    )

    assert response.status_code == 201, response.text

    result = await db_session.execute(
        select(User).where(
            User.email == test_user_payload["email"]
        )
    )

    user = result.scalar_one()

    assert user.is_active is True

    assert user.is_locked is False

    assert user.locked_at is None

    assert user.locked_reason is None