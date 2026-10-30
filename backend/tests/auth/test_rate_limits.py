from __future__ import annotations

import pytest
from httpx import AsyncClient


# =========================================================
# HELPERS
# =========================================================


async def signup_user(
    client: AsyncClient,
    payload: dict,
):
    response = await client.post(
        "/api/v1/auth/signup",
        json=payload,
    )

    return response


async def verify_email(
    client: AsyncClient,
    *,
    email: str,
):
    response = await client.post(
        "/api/v1/auth/verify-email",
        json={
            "email": email,
            "otp": "123456",
        },
    )

    return response


async def login_user(
    client: AsyncClient,
    *,
    identifier: str,
    password: str,
):
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "identifier": identifier,
            "password": password,
            "remember_me": False,
        },
    )

    return response


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


# =========================================================
# SIGNUP RATE LIMIT
# =========================================================


@pytest.mark.asyncio
async def test_signup_rate_limit_allows_normal_request(
    client: AsyncClient,
    test_user_payload,
):
    response = await signup_user(
        client,
        test_user_payload,
    )

    assert response.status_code == 201, response.text


@pytest.mark.asyncio
async def test_signup_rate_limit_does_not_break_validation(
    client: AsyncClient,
):
    response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "bad-email",
            "username": "ab",
            "password": "weak",
            "confirm_password": "different",
        },
    )

    assert response.status_code == 422, response.text


# =========================================================
# LOGIN RATE LIMIT
# =========================================================


@pytest.mark.asyncio
async def test_login_rate_limit_allows_valid_login(
    client: AsyncClient,
    test_user_payload,
):
    await create_verified_user(
        client,
        test_user_payload,
    )

    response = await login_user(
        client,
        identifier=test_user_payload["email"],
        password=test_user_payload["password"],
    )

    assert response.status_code == 200, response.text


@pytest.mark.asyncio
async def test_login_wrong_password_returns_auth_error(
    client: AsyncClient,
    test_user_payload,
):
    await create_verified_user(
        client,
        test_user_payload,
    )

    response = await login_user(
        client,
        identifier=test_user_payload["email"],
        password="WrongPassword123!",
    )

    assert response.status_code in {
        400,
        401,
        403,
        429,
    }, response.text


# =========================================================
# EMAIL VERIFICATION RATE LIMIT
# =========================================================


@pytest.mark.asyncio
async def test_verify_email_rate_limit_allows_valid_request(
    client: AsyncClient,
    test_user_payload,
):
    signup_response = await signup_user(
        client,
        test_user_payload,
    )

    assert signup_response.status_code == 201, signup_response.text

    verify_response = await verify_email(
        client,
        email=test_user_payload["email"],
    )

    assert verify_response.status_code == 200, verify_response.text


# =========================================================
# RESEND VERIFICATION RATE LIMIT
# =========================================================


@pytest.mark.asyncio
async def test_resend_verification_allows_normal_request(
    client: AsyncClient,
    test_user_payload,
):
    signup_response = await signup_user(
        client,
        test_user_payload,
    )

    assert signup_response.status_code == 201, signup_response.text

    response = await client.post(
        "/api/v1/auth/resend-verification",
        json={
            "email": test_user_payload["email"],
        },
    )

    assert response.status_code in {
        200,
        429,
    }, response.text


@pytest.mark.asyncio
async def test_resend_verification_unknown_user_is_safe(
    client: AsyncClient,
):
    response = await client.post(
        "/api/v1/auth/resend-verification",
        json={
            "email": "missing.user@example.com",
        },
    )

    assert response.status_code in {
        200,
        404,
        422,
        429,
    }, response.text


# =========================================================
# FORGOT PASSWORD RATE LIMIT
# =========================================================


@pytest.mark.asyncio
async def test_forgot_password_rate_limit_allows_normal_request(
    client: AsyncClient,
    test_user_payload,
):
    await create_verified_user(
        client,
        test_user_payload,
    )

    response = await client.post(
        "/api/v1/auth/forgot-password",
        json={
            "email": test_user_payload["email"],
        },
    )

    assert response.status_code in {
        200,
        429,
    }, response.text


@pytest.mark.asyncio
async def test_forgot_password_unknown_user_does_not_enumerate(
    client: AsyncClient,
):
    response = await client.post(
        "/api/v1/auth/forgot-password",
        json={
            "email": "missing.user@example.com",
        },
    )

    assert response.status_code in {
        200,
        429,
    }, response.text


# =========================================================
# VERIFY RESET OTP RATE LIMIT
# =========================================================


@pytest.mark.asyncio
async def test_verify_reset_otp_rate_limit_allows_valid_request(
    client: AsyncClient,
    test_user_payload,
):
    await create_verified_user(
        client,
        test_user_payload,
    )

    forgot_response = await client.post(
        "/api/v1/auth/forgot-password",
        json={
            "email": test_user_payload["email"],
        },
    )

    assert forgot_response.status_code == 200, forgot_response.text

    verify_response = await client.post(
        "/api/v1/auth/verify-reset-otp",
        json={
            "email": test_user_payload["email"],
            "otp": "123456",
        },
    )

    assert verify_response.status_code in {
        200,
        429,
    }, verify_response.text


# =========================================================
# INVALID OTP STILL FAILS CLEANLY
# =========================================================


@pytest.mark.asyncio
async def test_wrong_verification_otp_still_returns_auth_error(
    client: AsyncClient,
    test_user_payload,
):
    signup_response = await signup_user(
        client,
        test_user_payload,
    )

    assert signup_response.status_code == 201, signup_response.text

    response = await client.post(
        "/api/v1/auth/verify-email",
        json={
            "email": test_user_payload["email"],
            "otp": "654321",
        },
    )

    assert response.status_code in {
        400,
        401,
        422,
        429,
    }, response.text


# =========================================================
# RATE LIMIT RESPONSE CONTRACT
# =========================================================


@pytest.mark.asyncio
async def test_rate_limit_response_if_triggered_has_safe_error_shape(
    client: AsyncClient,
    test_user_payload,
):
    """
    This test intentionally does not force a production rate limit.

    Your test suite currently replaces the real Redis limiter with a
    fake limiter, so ordinary auth tests are deterministic.

    If the fake limiter or future test fixture is configured to return
    429, this verifies the response remains structured.
    """

    response = await signup_user(
        client,
        test_user_payload,
    )

    if response.status_code == 429:
        data = response.json()

        assert "error" in data
        assert isinstance(
            data["error"],
            dict,
        )

        assert (
            data["error"].get("code")
            or data["error"].get("message")
        )

    else:
        assert response.status_code == 201, response.text


# =========================================================
# RETRY-AFTER HEADER IF PRESENT
# =========================================================


@pytest.mark.asyncio
async def test_rate_limit_retry_after_header_is_valid_if_present(
    client: AsyncClient,
    test_user_payload,
):
    response = await signup_user(
        client,
        test_user_payload,
    )

    retry_after = response.headers.get(
        "Retry-After"
    )

    if retry_after is not None:
        assert retry_after.strip()

        try:
            retry_seconds = int(
                retry_after
            )
        except ValueError:
            # HTTP Retry-After may also legally be an HTTP-date.
            assert len(retry_after) > 0

        else:
            assert retry_seconds >= 0


# =========================================================
# DIFFERENT AUTH ENDPOINTS REMAIN AVAILABLE
# =========================================================


@pytest.mark.asyncio
async def test_auth_endpoints_are_not_globally_blocked(
    client: AsyncClient,
    test_user_payload,
):
    """
    A rate limiter must not accidentally block the entire auth module
    after one request.
    """

    signup_response = await signup_user(
        client,
        test_user_payload,
    )

    assert signup_response.status_code == 201, signup_response.text

    verify_response = await verify_email(
        client,
        email=test_user_payload["email"],
    )

    assert verify_response.status_code == 200, verify_response.text

    login_response = await login_user(
        client,
        identifier=test_user_payload["email"],
        password=test_user_payload["password"],
    )

    assert login_response.status_code == 200, login_response.text


# =========================================================
# RATE LIMIT SHOULD NOT EXPOSE INTERNAL DETAILS
# =========================================================


@pytest.mark.asyncio
async def test_auth_error_does_not_expose_redis_details(
    client: AsyncClient,
    test_user_payload,
):
    response = await login_user(
        client,
        identifier=test_user_payload["email"],
        password="WrongPassword123!",
    )

    body = response.text.lower()

    assert "redis://" not in body
    assert "localhost:6381" not in body
    assert "traceback" not in body


# =========================================================
# RATE LIMIT SHOULD NOT EXPOSE SECRETS
# =========================================================


@pytest.mark.asyncio
async def test_rate_limit_error_does_not_expose_secrets(
    client: AsyncClient,
):
    response = await client.post(
        "/api/v1/auth/forgot-password",
        json={
            "email": "missing.user@example.com",
        },
    )

    body = response.text.lower()

    assert "jwt_secret" not in body
    assert "smtp_password" not in body
    assert "database_url" not in body


# =========================================================
# INVALID EMAIL STILL VALIDATED BEFORE NORMAL FLOW
# =========================================================


@pytest.mark.asyncio
async def test_invalid_email_request_is_rejected_safely(
    client: AsyncClient,
):
    response = await client.post(
        "/api/v1/auth/forgot-password",
        json={
            "email": "invalid-email",
        },
    )

    assert response.status_code == 422, response.text


# =========================================================
# EMPTY LOGIN IDENTIFIER
# =========================================================


@pytest.mark.asyncio
async def test_empty_login_identifier_is_validation_error(
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
# RATE-LIMIT TEST FILE MUST NOT DEPEND ON REAL REDIS STATE
# =========================================================


@pytest.mark.asyncio
async def test_normal_auth_request_is_deterministic_in_test_environment(
    client: AsyncClient,
    test_user_payload,
):
    """
    conftest.py replaces the production rate-limit behavior during
    ordinary auth tests.

    This prevents previous local Redis keys from making tests flaky.
    """

    response = await signup_user(
        client,
        test_user_payload,
    )

    assert response.status_code == 201, response.text