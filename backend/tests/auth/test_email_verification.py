from __future__ import annotations

from datetime import timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.modules.auth.models import (
    EmailVerificationChallenge,
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


async def get_verification_challenges(
    db_session,
    user_id,
) -> list[EmailVerificationChallenge]:
    result = await db_session.execute(
        select(EmailVerificationChallenge)
        .where(
            EmailVerificationChallenge.user_id == user_id
        )
        .order_by(
            EmailVerificationChallenge.created_at.desc()
        )
    )

    return list(
        result.scalars().all()
    )


# =========================================================
# VALID OTP
# =========================================================


@pytest.mark.asyncio
async def test_verify_email_success(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    signup_response = await client.post(
        "/api/v1/auth/signup",
        json=test_user_payload,
    )

    assert signup_response.status_code == 201, signup_response.text

    verify_response = await client.post(
        "/api/v1/auth/verify-email",
        json={
            "email": test_user_payload["email"],
            "otp": "123456",
        },
    )

    assert verify_response.status_code == 200, verify_response.text

    await db_session.rollback()

    user = await get_user_by_email(
        db_session,
        test_user_payload["email"],
    )

    assert user.is_email_verified is True
    assert user.email_verified_at is not None


# =========================================================
# CHALLENGE CONSUMED AFTER SUCCESS
# =========================================================


@pytest.mark.asyncio
async def test_verify_email_consumes_challenge(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    signup_response = await client.post(
        "/api/v1/auth/signup",
        json=test_user_payload,
    )

    assert signup_response.status_code == 201

    verify_response = await client.post(
        "/api/v1/auth/verify-email",
        json={
            "email": test_user_payload["email"],
            "otp": "123456",
        },
    )

    assert verify_response.status_code == 200, verify_response.text

    await db_session.rollback()

    user = await get_user_by_email(
        db_session,
        test_user_payload["email"],
    )

    user_id = user.id

    challenges = await get_verification_challenges(
        db_session,
        user_id,
    )

    assert len(challenges) == 1

    challenge = challenges[0]

    assert challenge.verified_at is not None
    assert challenge.consumed_at is not None


# =========================================================
# WRONG OTP
# =========================================================


@pytest.mark.asyncio
async def test_verify_email_wrong_otp_rejected(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    signup_response = await client.post(
        "/api/v1/auth/signup",
        json=test_user_payload,
    )

    assert signup_response.status_code == 201

    verify_response = await client.post(
        "/api/v1/auth/verify-email",
        json={
            "email": test_user_payload["email"],
            "otp": "654321",
        },
    )

    assert verify_response.status_code == 422, verify_response.text

    data = verify_response.json()

    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "invalid otp" in data["error"]["message"].lower()

    await db_session.rollback()

    user = await get_user_by_email(
        db_session,
        test_user_payload["email"],
    )

    assert user.is_email_verified is False
    assert user.email_verified_at is None


# =========================================================
# WRONG OTP INCREMENTS ATTEMPT COUNT
# =========================================================


@pytest.mark.asyncio
async def test_wrong_otp_increments_attempt_count(
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
        "/api/v1/auth/verify-email",
        json={
            "email": test_user_payload["email"],
            "otp": "654321",
        },
    )

    assert response.status_code == 422, response.text

    await db_session.rollback()

    user = await get_user_by_email(
        db_session,
        test_user_payload["email"],
    )

    user_id = user.id

    challenges = await get_verification_challenges(
        db_session,
        user_id,
    )

    assert len(challenges) == 1

    challenge = challenges[0]

    # IMPORTANT:
    # This must remain 1.
    # If it remains 0, the backend is rolling back the failed-attempt
    # increment instead of persisting it.
    assert challenge.attempt_count == 1


# =========================================================
# MULTIPLE WRONG ATTEMPTS
# =========================================================


@pytest.mark.asyncio
async def test_multiple_wrong_otps_increment_attempt_count(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    signup_response = await client.post(
        "/api/v1/auth/signup",
        json=test_user_payload,
    )

    assert signup_response.status_code == 201

    first_response = await client.post(
        "/api/v1/auth/verify-email",
        json={
            "email": test_user_payload["email"],
            "otp": "654321",
        },
    )

    assert first_response.status_code == 422, first_response.text

    second_response = await client.post(
        "/api/v1/auth/verify-email",
        json={
            "email": test_user_payload["email"],
            "otp": "654321",
        },
    )

    assert second_response.status_code == 422, second_response.text

    await db_session.rollback()

    user = await get_user_by_email(
        db_session,
        test_user_payload["email"],
    )

    user_id = user.id

    challenges = await get_verification_challenges(
        db_session,
        user_id,
    )

    assert len(challenges) == 1

    challenge = challenges[0]

    assert challenge.attempt_count == 2


# =========================================================
# OTP FORMAT VALIDATION
# =========================================================


@pytest.mark.asyncio
async def test_verify_email_short_otp_rejected(
    client: AsyncClient,
    test_user_payload,
):
    signup_response = await client.post(
        "/api/v1/auth/signup",
        json=test_user_payload,
    )

    assert signup_response.status_code == 201

    response = await client.post(
        "/api/v1/auth/verify-email",
        json={
            "email": test_user_payload["email"],
            "otp": "123",
        },
    )

    assert response.status_code == 422, response.text

    data = response.json()

    assert data["error"]["code"] == "VALIDATION_ERROR"


# =========================================================
# INVALID EMAIL FORMAT
# =========================================================


@pytest.mark.asyncio
async def test_verify_email_invalid_email_rejected(
    client: AsyncClient,
):
    response = await client.post(
        "/api/v1/auth/verify-email",
        json={
            "email": "not-an-email",
            "otp": "123456",
        },
    )

    assert response.status_code == 422, response.text

    data = response.json()

    assert data["error"]["code"] == "VALIDATION_ERROR"


# =========================================================
# UNKNOWN ACCOUNT
# =========================================================


@pytest.mark.asyncio
async def test_verify_email_unknown_user_rejected(
    client: AsyncClient,
):
    response = await client.post(
        "/api/v1/auth/verify-email",
        json={
            "email": "unknown.user@example.com",
            "otp": "123456",
        },
    )

    assert response.status_code in {
        400,
        404,
        422,
    }, response.text


# =========================================================
# OTP CAN ONLY BE USED ONCE
# =========================================================


@pytest.mark.asyncio
async def test_verification_otp_cannot_be_reused(
    client: AsyncClient,
    test_user_payload,
):
    signup_response = await client.post(
        "/api/v1/auth/signup",
        json=test_user_payload,
    )

    assert signup_response.status_code == 201

    first_verify = await client.post(
        "/api/v1/auth/verify-email",
        json={
            "email": test_user_payload["email"],
            "otp": "123456",
        },
    )

    assert first_verify.status_code == 200, first_verify.text

    second_verify = await client.post(
        "/api/v1/auth/verify-email",
        json={
            "email": test_user_payload["email"],
            "otp": "123456",
        },
    )

    assert second_verify.status_code in {
        400,
        409,
        422,
    }, second_verify.text


# =========================================================
# RESEND VERIFICATION CREATES NEW CHALLENGE
# =========================================================


@pytest.mark.asyncio
async def test_resend_verification_creates_new_challenge(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    signup_response = await client.post(
        "/api/v1/auth/signup",
        json=test_user_payload,
    )

    assert signup_response.status_code == 201

    await db_session.rollback()

    user = await get_user_by_email(
        db_session,
        test_user_payload["email"],
    )

    # Store plain UUID before rollback.
    # Do NOT use user.id after rollback.
    user_id = user.id

    initial_challenges = await get_verification_challenges(
        db_session,
        user_id,
    )

    assert len(initial_challenges) == 1

    first_challenge_id = initial_challenges[0].id

    await db_session.rollback()

    resend_response = await client.post(
        "/api/v1/auth/resend-verification",
        json={
            "email": test_user_payload["email"],
        },
    )

    assert resend_response.status_code == 200, resend_response.text

    await db_session.rollback()

    challenges = await get_verification_challenges(
        db_session,
        user_id,
    )

    assert len(challenges) == 2

    newest_challenge = challenges[0]

    assert newest_challenge.id != first_challenge_id


# =========================================================
# RESEND INVALIDATES OLD CHALLENGE
# =========================================================


@pytest.mark.asyncio
async def test_resend_verification_invalidates_old_challenge(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    signup_response = await client.post(
        "/api/v1/auth/signup",
        json=test_user_payload,
    )

    assert signup_response.status_code == 201

    await db_session.rollback()

    user = await get_user_by_email(
        db_session,
        test_user_payload["email"],
    )

    user_id = user.id

    initial_challenges = await get_verification_challenges(
        db_session,
        user_id,
    )

    assert len(initial_challenges) == 1

    first_challenge_id = initial_challenges[0].id

    await db_session.rollback()

    resend_response = await client.post(
        "/api/v1/auth/resend-verification",
        json={
            "email": test_user_payload["email"],
        },
    )

    assert resend_response.status_code == 200, resend_response.text

    await db_session.rollback()

    challenges = await get_verification_challenges(
        db_session,
        user_id,
    )

    assert len(challenges) == 2

    old_challenge = next(
        challenge
        for challenge in challenges
        if challenge.id == first_challenge_id
    )

    new_challenge = next(
        challenge
        for challenge in challenges
        if challenge.id != first_challenge_id
    )

    assert old_challenge.invalidated_at is not None

    assert new_challenge.invalidated_at is None
    assert new_challenge.consumed_at is None
    assert new_challenge.verified_at is None


# =========================================================
# OLD CHALLENGE CANNOT BE USED AFTER RESEND
# =========================================================


@pytest.mark.asyncio
async def test_old_challenge_is_invalidated_after_resend(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    signup_response = await client.post(
        "/api/v1/auth/signup",
        json=test_user_payload,
    )

    assert signup_response.status_code == 201

    await db_session.rollback()

    user = await get_user_by_email(
        db_session,
        test_user_payload["email"],
    )

    user_id = user.id

    initial_challenges = await get_verification_challenges(
        db_session,
        user_id,
    )

    assert len(initial_challenges) == 1

    old_challenge_id = initial_challenges[0].id

    await db_session.rollback()

    resend_response = await client.post(
        "/api/v1/auth/resend-verification",
        json={
            "email": test_user_payload["email"],
        },
    )

    assert resend_response.status_code == 200, resend_response.text

    await db_session.rollback()

    challenges = await get_verification_challenges(
        db_session,
        user_id,
    )

    old_challenge = next(
        challenge
        for challenge in challenges
        if challenge.id == old_challenge_id
    )

    assert old_challenge.invalidated_at is not None


# =========================================================
# NEW OTP AFTER RESEND WORKS
# =========================================================


@pytest.mark.asyncio
async def test_new_verification_challenge_after_resend_works(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    signup_response = await client.post(
        "/api/v1/auth/signup",
        json=test_user_payload,
    )

    assert signup_response.status_code == 201

    resend_response = await client.post(
        "/api/v1/auth/resend-verification",
        json={
            "email": test_user_payload["email"],
        },
    )

    assert resend_response.status_code == 200, resend_response.text

    verify_response = await client.post(
        "/api/v1/auth/verify-email",
        json={
            "email": test_user_payload["email"],
            "otp": "123456",
        },
    )

    assert verify_response.status_code == 200, verify_response.text

    await db_session.rollback()

    user = await get_user_by_email(
        db_session,
        test_user_payload["email"],
    )

    assert user.is_email_verified is True
    assert user.email_verified_at is not None


# =========================================================
# ALREADY VERIFIED USER CANNOT RESEND
# =========================================================


@pytest.mark.asyncio
async def test_resend_verification_for_verified_user_rejected(
    client: AsyncClient,
    test_user_payload,
):
    signup_response = await client.post(
        "/api/v1/auth/signup",
        json=test_user_payload,
    )

    assert signup_response.status_code == 201

    verify_response = await client.post(
        "/api/v1/auth/verify-email",
        json={
            "email": test_user_payload["email"],
            "otp": "123456",
        },
    )

    assert verify_response.status_code == 200

    resend_response = await client.post(
        "/api/v1/auth/resend-verification",
        json={
            "email": test_user_payload["email"],
        },
    )

    assert resend_response.status_code in {
        400,
        409,
        422,
    }, resend_response.text


# =========================================================
# RESEND UNKNOWN USER
# =========================================================


@pytest.mark.asyncio
async def test_resend_verification_unknown_user_safe_response(
    client: AsyncClient,
):
    response = await client.post(
        "/api/v1/auth/resend-verification",
        json={
            "email": "does.not.exist@example.com",
        },
    )

    # Either generic anti-enumeration response or explicit
    # not-found/validation response is accepted by this test.
    assert response.status_code in {
        200,
        404,
        422,
    }, response.text


# =========================================================
# EXPIRED CHALLENGE
# =========================================================


@pytest.mark.asyncio
async def test_expired_verification_otp_rejected(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    signup_response = await client.post(
        "/api/v1/auth/signup",
        json=test_user_payload,
    )

    assert signup_response.status_code == 201

    await db_session.rollback()

    user = await get_user_by_email(
        db_session,
        test_user_payload["email"],
    )

    user_id = user.id

    challenges = await get_verification_challenges(
        db_session,
        user_id,
    )

    assert len(challenges) == 1

    challenge = challenges[0]

    challenge.expires_at = (
        challenge.created_at
        - timedelta(minutes=1)
    )

    await db_session.commit()

    response = await client.post(
        "/api/v1/auth/verify-email",
        json={
            "email": test_user_payload["email"],
            "otp": "123456",
        },
    )

    # Your production API intentionally maps this condition
    # to VALIDATION_ERROR / HTTP 422.
    assert response.status_code == 422, response.text

    data = response.json()

    assert data["error"]["code"] == "VALIDATION_ERROR"

    assert "expired" in (
        data["error"]["message"].lower()
    )

    await db_session.rollback()

    user = await get_user_by_email(
        db_session,
        test_user_payload["email"],
    )

    assert user.is_email_verified is False
    assert user.email_verified_at is None


# =========================================================
# EXPIRED OTP DOES NOT VERIFY CHALLENGE
# =========================================================


@pytest.mark.asyncio
async def test_expired_challenge_remains_unverified(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    signup_response = await client.post(
        "/api/v1/auth/signup",
        json=test_user_payload,
    )

    assert signup_response.status_code == 201

    await db_session.rollback()

    user = await get_user_by_email(
        db_session,
        test_user_payload["email"],
    )

    user_id = user.id

    challenges = await get_verification_challenges(
        db_session,
        user_id,
    )

    assert len(challenges) == 1

    challenge = challenges[0]

    challenge.expires_at = (
        challenge.created_at
        - timedelta(minutes=1)
    )

    challenge_id = challenge.id

    await db_session.commit()

    response = await client.post(
        "/api/v1/auth/verify-email",
        json={
            "email": test_user_payload["email"],
            "otp": "123456",
        },
    )

    assert response.status_code == 422, response.text

    await db_session.rollback()

    result = await db_session.execute(
        select(EmailVerificationChallenge).where(
            EmailVerificationChallenge.id == challenge_id
        )
    )

    challenge = result.scalar_one()

    assert challenge.verified_at is None
    assert challenge.consumed_at is None


# =========================================================
# OTP HASH NEVER PLAINTEXT ON INITIAL SIGNUP
# =========================================================


@pytest.mark.asyncio
async def test_initial_verification_does_not_store_plaintext_otp(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    signup_response = await client.post(
        "/api/v1/auth/signup",
        json=test_user_payload,
    )

    assert signup_response.status_code == 201

    await db_session.rollback()

    user = await get_user_by_email(
        db_session,
        test_user_payload["email"],
    )

    user_id = user.id

    challenges = await get_verification_challenges(
        db_session,
        user_id,
    )

    assert len(challenges) == 1

    challenge = challenges[0]

    assert challenge.otp_hash is not None
    assert challenge.otp_hash != "123456"
    assert "123456" not in challenge.otp_hash


# =========================================================
# OTP HASH NEVER PLAINTEXT AFTER RESEND
# =========================================================


@pytest.mark.asyncio
async def test_resend_does_not_store_plaintext_otp(
    client: AsyncClient,
    db_session,
    test_user_payload,
):
    signup_response = await client.post(
        "/api/v1/auth/signup",
        json=test_user_payload,
    )

    assert signup_response.status_code == 201

    resend_response = await client.post(
        "/api/v1/auth/resend-verification",
        json={
            "email": test_user_payload["email"],
        },
    )

    assert resend_response.status_code == 200, resend_response.text

    await db_session.rollback()

    user = await get_user_by_email(
        db_session,
        test_user_payload["email"],
    )

    user_id = user.id

    challenges = await get_verification_challenges(
        db_session,
        user_id,
    )

    assert len(challenges) == 2

    newest_challenge = challenges[0]

    assert newest_challenge.otp_hash is not None
    assert newest_challenge.otp_hash != "123456"
    assert "123456" not in newest_challenge.otp_hash