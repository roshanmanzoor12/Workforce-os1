from __future__ import annotations

from urllib.parse import parse_qs, urlparse

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select

from app.config import settings
from app.modules.auth.google_oauth import GoogleUserProfile
from app.modules.auth.models import (
    AuthIdentity,
    RefreshSession,
    User,
)


# =========================================================
# TEST CONSTANTS
# =========================================================


GOOGLE_CLIENT_ID = "test-google-client-id"
GOOGLE_CLIENT_SECRET = "test-google-client-secret"
GOOGLE_REDIRECT_URI = (
    "http://testserver/api/v1/auth/oauth/google/callback"
)

GOOGLE_PROVIDER_SUBJECT = "google-user-123456789"

GOOGLE_EMAIL = "oauth.google.user@example.com"


# =========================================================
# HELPERS
# =========================================================


def configure_google_settings(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        settings,
        "google_client_id",
        GOOGLE_CLIENT_ID,
    )

    monkeypatch.setattr(
        settings,
        "google_client_secret",
        GOOGLE_CLIENT_SECRET,
    )

    monkeypatch.setattr(
        settings,
        "google_redirect_uri",
        GOOGLE_REDIRECT_URI,
    )


def make_google_profile(
    *,
    provider_user_id: str = GOOGLE_PROVIDER_SUBJECT,
    email: str = GOOGLE_EMAIL,
    email_verified: bool = True,
    first_name: str | None = "Google",
    last_name: str | None = "User",
    display_name: str | None = "Google User",
    avatar_url: str | None = "https://example.com/avatar.png",
) -> GoogleUserProfile:
    return GoogleUserProfile(
        provider="google",
        provider_user_id=provider_user_id,
        email=email,
        email_verified=email_verified,
        first_name=first_name,
        last_name=last_name,
        display_name=display_name,
        avatar_url=avatar_url,
        locale="en",
    )


async def mock_google_authentication(
    monkeypatch,
    profile: GoogleUserProfile,
) -> None:
    async def fake_authenticate_google_authorization_code(
        **kwargs,
    ):
        return (
            profile,
            object(),
        )

    monkeypatch.setattr(
        "app.modules.auth.service."
        "authenticate_google_authorization_code",
        fake_authenticate_google_authorization_code,
    )


async def get_google_authorization(
    client: AsyncClient,
):
    return await client.get(
        "/api/v1/auth/oauth/google/authorize"
    )


async def get_google_state(
    client: AsyncClient,
) -> str:
    response = await get_google_authorization(
        client
    )

    assert response.status_code == 200, response.text

    data = response.json()

    authorization_url = data[
        "authorization_url"
    ]

    parsed = urlparse(
        authorization_url
    )

    query = parse_qs(
        parsed.query
    )

    states = query.get(
        "state"
    )

    assert states
    assert states[0]

    return states[0]


async def complete_google_callback(
    client: AsyncClient,
    *,
    state: str,
    code: str = "test-google-authorization-code",
):
    return await client.get(
        "/api/v1/auth/oauth/google/callback",
        params={
            "code": code,
            "state": state,
        },
    )


async def create_local_verified_user(
    client: AsyncClient,
    payload: dict,
) -> None:
    signup_response = await client.post(
        "/api/v1/auth/signup",
        json=payload,
    )

    assert signup_response.status_code == 201, (
        signup_response.text
    )

    verify_response = await client.post(
        "/api/v1/auth/verify-email",
        json={
            "email": payload["email"],
            "otp": "123456",
        },
    )

    assert verify_response.status_code == 200, (
        verify_response.text
    )


# =========================================================
# GOOGLE AUTHORIZATION
# =========================================================


@pytest.mark.asyncio
async def test_google_authorization_endpoint_returns_url(
    client: AsyncClient,
    monkeypatch,
):
    configure_google_settings(
        monkeypatch
    )

    response = await get_google_authorization(
        client
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["provider"] == "google"

    authorization_url = data[
        "authorization_url"
    ]

    assert authorization_url

    parsed = urlparse(
        authorization_url
    )

    assert parsed.scheme == "https"
    assert parsed.netloc == "accounts.google.com"

    query = parse_qs(
        parsed.query
    )

    assert query["client_id"][0] == GOOGLE_CLIENT_ID
    assert query["redirect_uri"][0] == GOOGLE_REDIRECT_URI
    assert query["response_type"][0] == "code"

    assert query.get(
        "state"
    )


@pytest.mark.asyncio
async def test_google_authorization_url_requests_required_scopes(
    client: AsyncClient,
    monkeypatch,
):
    configure_google_settings(
        monkeypatch
    )

    response = await get_google_authorization(
        client
    )

    assert response.status_code == 200, response.text

    authorization_url = response.json()[
        "authorization_url"
    ]

    query = parse_qs(
        urlparse(
            authorization_url
        ).query
    )

    scope = query["scope"][0].split()

    assert "openid" in scope
    assert "email" in scope
    assert "profile" in scope


@pytest.mark.asyncio
async def test_google_authorization_generates_state(
    client: AsyncClient,
    monkeypatch,
):
    configure_google_settings(
        monkeypatch
    )

    first_state = await get_google_state(
        client
    )

    second_state = await get_google_state(
        client
    )

    assert first_state
    assert second_state
    assert first_state != second_state


# =========================================================
# CALLBACK VALIDATION
# =========================================================


@pytest.mark.asyncio
async def test_google_callback_requires_code(
    client: AsyncClient,
    monkeypatch,
):
    configure_google_settings(
        monkeypatch
    )

    state = await get_google_state(
        client
    )

    response = await client.get(
        "/api/v1/auth/oauth/google/callback",
        params={
            "state": state,
        },
    )

    assert response.status_code == 422, response.text


@pytest.mark.asyncio
async def test_google_callback_requires_state(
    client: AsyncClient,
    monkeypatch,
):
    configure_google_settings(
        monkeypatch
    )

    response = await client.get(
        "/api/v1/auth/oauth/google/callback",
        params={
            "code": "test-code",
        },
    )

    assert response.status_code == 422, response.text


@pytest.mark.asyncio
async def test_google_callback_rejects_invalid_state(
    client: AsyncClient,
    monkeypatch,
):
    configure_google_settings(
        monkeypatch
    )

    async def provider_must_not_be_called(
        **kwargs,
    ):
        raise AssertionError(
            "Google provider must not be called "
            "when OAuth state is invalid."
        )

    monkeypatch.setattr(
        "app.modules.auth.service."
        "authenticate_google_authorization_code",
        provider_must_not_be_called,
    )

    response = await complete_google_callback(
        client,
        state="invalid-google-oauth-state-value",
    )

    assert response.status_code in {
        400,
        401,
        403,
    }, response.text


@pytest.mark.asyncio
async def test_google_callback_rejects_unverified_provider_email(
    client: AsyncClient,
    monkeypatch,
):
    configure_google_settings(
        monkeypatch
    )

    profile = make_google_profile(
        email_verified=False,
    )

    await mock_google_authentication(
        monkeypatch,
        profile,
    )

    state = await get_google_state(
        client
    )

    response = await complete_google_callback(
        client,
        state=state,
    )

    assert response.status_code in {
        400,
        401,
        403,
    }, response.text


# =========================================================
# NEW GOOGLE USER
# =========================================================


@pytest.mark.asyncio
async def test_google_callback_creates_new_global_user(
    client: AsyncClient,
    db_session,
    monkeypatch,
):
    configure_google_settings(
        monkeypatch
    )

    profile = make_google_profile()

    await mock_google_authentication(
        monkeypatch,
        profile,
    )

    state = await get_google_state(
        client
    )

    response = await complete_google_callback(
        client,
        state=state,
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["provider"] == "google"
    assert data["is_new_user"] is True

    user_data = data["user"]

    assert user_data["email"] == GOOGLE_EMAIL
    assert user_data["is_email_verified"] is True
    assert user_data["is_active"] is True

    result = await db_session.execute(
        select(User).where(
            User.email == GOOGLE_EMAIL
        )
    )

    user = result.scalar_one_or_none()

    assert user is not None
    assert user.email == GOOGLE_EMAIL
    assert user.is_email_verified is True
    assert user.password_hash is None


@pytest.mark.asyncio
async def test_google_callback_creates_auth_identity(
    client: AsyncClient,
    db_session,
    monkeypatch,
):
    configure_google_settings(
        monkeypatch
    )

    profile = make_google_profile()

    await mock_google_authentication(
        monkeypatch,
        profile,
    )

    state = await get_google_state(
        client
    )

    response = await complete_google_callback(
        client,
        state=state,
    )

    assert response.status_code == 200, response.text

    result = await db_session.execute(
        select(AuthIdentity).where(
            AuthIdentity.provider == "google",
            AuthIdentity.provider_subject
            == GOOGLE_PROVIDER_SUBJECT,
        )
    )

    identity = result.scalar_one_or_none()

    assert identity is not None
    assert identity.provider == "google"
    assert (
        identity.provider_subject
        == GOOGLE_PROVIDER_SUBJECT
    )
    assert identity.provider_email == GOOGLE_EMAIL


@pytest.mark.asyncio
async def test_google_callback_returns_workforce_tokens(
    client: AsyncClient,
    monkeypatch,
):
    configure_google_settings(
        monkeypatch
    )

    profile = make_google_profile()

    await mock_google_authentication(
        monkeypatch,
        profile,
    )

    state = await get_google_state(
        client
    )

    response = await complete_google_callback(
        client,
        state=state,
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["access_token"]
    assert data["refresh_token"]
    assert data["access_token"] != data["refresh_token"]
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0


@pytest.mark.asyncio
async def test_google_callback_creates_refresh_session(
    client: AsyncClient,
    db_session,
    monkeypatch,
):
    configure_google_settings(
        monkeypatch
    )

    profile = make_google_profile()

    await mock_google_authentication(
        monkeypatch,
        profile,
    )

    state = await get_google_state(
        client
    )

    response = await complete_google_callback(
        client,
        state=state,
    )

    assert response.status_code == 200, response.text

    data = response.json()

    refresh_token = data[
        "refresh_token"
    ]

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

    for token_hash in stored_hashes:
        assert token_hash
        assert token_hash != refresh_token


@pytest.mark.asyncio
async def test_google_access_token_authenticates_me(
    client: AsyncClient,
    monkeypatch,
):
    configure_google_settings(
        monkeypatch
    )

    profile = make_google_profile()

    await mock_google_authentication(
        monkeypatch,
        profile,
    )

    state = await get_google_state(
        client
    )

    callback_response = await complete_google_callback(
        client,
        state=state,
    )

    assert callback_response.status_code == 200, (
        callback_response.text
    )

    access_token = callback_response.json()[
        "access_token"
    ]

    response = await client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": (
                f"Bearer {access_token}"
            )
        },
    )

    assert response.status_code == 200, response.text

    data = response.json()

    user = (
        data.get("user")
        if isinstance(data, dict)
        else data
    )

    assert user
    assert user["email"] == GOOGLE_EMAIL


# =========================================================
# EXISTING GLOBAL USER LINKING
# =========================================================


@pytest.mark.asyncio
async def test_google_login_links_existing_user_by_verified_email(
    client: AsyncClient,
    db_session,
    monkeypatch,
    test_user_payload,
):
    configure_google_settings(
        monkeypatch
    )

    await create_local_verified_user(
        client,
        test_user_payload,
    )

    profile = make_google_profile(
        email=test_user_payload["email"],
    )

    await mock_google_authentication(
        monkeypatch,
        profile,
    )

    state = await get_google_state(
        client
    )

    response = await complete_google_callback(
        client,
        state=state,
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["is_new_user"] is False

    result = await db_session.execute(
        select(
            func.count(
                User.id
            )
        ).where(
            User.email
            == test_user_payload["email"]
        )
    )

    user_count = result.scalar_one()

    assert user_count == 1

    identity_result = await db_session.execute(
        select(AuthIdentity).where(
            AuthIdentity.provider == "google",
            AuthIdentity.provider_subject
            == GOOGLE_PROVIDER_SUBJECT,
        )
    )

    identity = identity_result.scalar_one_or_none()

    assert identity is not None


@pytest.mark.asyncio
async def test_google_login_marks_existing_unverified_email_verified(
    client: AsyncClient,
    db_session,
    monkeypatch,
    test_user_payload,
):
    configure_google_settings(
        monkeypatch
    )

    signup_response = await client.post(
        "/api/v1/auth/signup",
        json=test_user_payload,
    )

    assert signup_response.status_code == 201, (
        signup_response.text
    )

    profile = make_google_profile(
        email=test_user_payload["email"],
    )

    await mock_google_authentication(
        monkeypatch,
        profile,
    )

    state = await get_google_state(
        client
    )

    response = await complete_google_callback(
        client,
        state=state,
    )

    assert response.status_code == 200, response.text

    result = await db_session.execute(
        select(User).where(
            User.email
            == test_user_payload["email"]
        )
    )

    user = result.scalar_one()

    assert user.is_email_verified is True
    assert user.email_verified_at is not None


# =========================================================
# EXISTING GOOGLE IDENTITY
# =========================================================


@pytest.mark.asyncio
async def test_second_google_login_reuses_existing_identity(
    client: AsyncClient,
    db_session,
    monkeypatch,
):
    configure_google_settings(
        monkeypatch
    )

    profile = make_google_profile()

    await mock_google_authentication(
        monkeypatch,
        profile,
    )

    first_state = await get_google_state(
        client
    )

    first_response = await complete_google_callback(
        client,
        state=first_state,
    )

    assert first_response.status_code == 200, (
        first_response.text
    )

    assert first_response.json()[
        "is_new_user"
    ] is True

    second_state = await get_google_state(
        client
    )

    second_response = await complete_google_callback(
        client,
        state=second_state,
    )

    assert second_response.status_code == 200, (
        second_response.text
    )

    assert second_response.json()[
        "is_new_user"
    ] is False

    result = await db_session.execute(
        select(
            func.count(
                AuthIdentity.id
            )
        ).where(
            AuthIdentity.provider == "google",
            AuthIdentity.provider_subject
            == GOOGLE_PROVIDER_SUBJECT,
        )
    )

    identity_count = result.scalar_one()

    assert identity_count == 1


@pytest.mark.asyncio
async def test_second_google_login_reuses_same_global_user(
    client: AsyncClient,
    db_session,
    monkeypatch,
):
    configure_google_settings(
        monkeypatch
    )

    profile = make_google_profile()

    await mock_google_authentication(
        monkeypatch,
        profile,
    )

    first_state = await get_google_state(
        client
    )

    first_response = await complete_google_callback(
        client,
        state=first_state,
    )

    assert first_response.status_code == 200, (
        first_response.text
    )

    first_user_id = first_response.json()[
        "user"
    ]["id"]

    second_state = await get_google_state(
        client
    )

    second_response = await complete_google_callback(
        client,
        state=second_state,
    )

    assert second_response.status_code == 200, (
        second_response.text
    )

    second_user_id = second_response.json()[
        "user"
    ]["id"]

    assert second_user_id == first_user_id

    result = await db_session.execute(
        select(
            func.count(
                User.id
            )
        ).where(
            User.email == GOOGLE_EMAIL
        )
    )

    user_count = result.scalar_one()

    assert user_count == 1


# =========================================================
# PROVIDER TOKEN / SECRET EXPOSURE
# =========================================================


@pytest.mark.asyncio
async def test_google_callback_does_not_expose_provider_tokens(
    client: AsyncClient,
    monkeypatch,
):
    configure_google_settings(
        monkeypatch
    )

    profile = make_google_profile()

    class FakeProviderTokens:
        access_token = (
            "google-provider-access-token-secret"
        )
        refresh_token = (
            "google-provider-refresh-token-secret"
        )
        id_token = (
            "google-provider-id-token-secret"
        )

    async def fake_authenticate_google_authorization_code(
        **kwargs,
    ):
        return (
            profile,
            FakeProviderTokens(),
        )

    monkeypatch.setattr(
        "app.modules.auth.service."
        "authenticate_google_authorization_code",
        fake_authenticate_google_authorization_code,
    )

    state = await get_google_state(
        client
    )

    response = await complete_google_callback(
        client,
        state=state,
    )

    assert response.status_code == 200, response.text

    body = response.text

    assert (
        "google-provider-access-token-secret"
        not in body
    )

    assert (
        "google-provider-refresh-token-secret"
        not in body
    )

    assert (
        "google-provider-id-token-secret"
        not in body
    )

    data = response.json()

    assert "provider_access_token" not in data
    assert "provider_refresh_token" not in data
    assert "id_token" not in data


@pytest.mark.asyncio
async def test_google_callback_does_not_expose_google_client_secret(
    client: AsyncClient,
    monkeypatch,
):
    configure_google_settings(
        monkeypatch
    )

    profile = make_google_profile()

    await mock_google_authentication(
        monkeypatch,
        profile,
    )

    state = await get_google_state(
        client
    )

    response = await complete_google_callback(
        client,
        state=state,
    )

    assert response.status_code == 200, response.text

    assert GOOGLE_CLIENT_SECRET not in response.text


# =========================================================
# USERNAME ALLOCATION
# =========================================================


@pytest.mark.asyncio
async def test_new_google_user_receives_username(
    client: AsyncClient,
    monkeypatch,
):
    configure_google_settings(
        monkeypatch
    )

    profile = make_google_profile(
        email="google.oauth.person@example.com",
    )

    await mock_google_authentication(
        monkeypatch,
        profile,
    )

    state = await get_google_state(
        client
    )

    response = await complete_google_callback(
        client,
        state=state,
    )

    assert response.status_code == 200, response.text

    username = response.json()[
        "user"
    ]["username"]

    assert username
    assert len(username) >= 3


# =========================================================
# SESSION METADATA
# =========================================================


@pytest.mark.asyncio
async def test_google_login_stores_request_session_metadata(
    client: AsyncClient,
    db_session,
    monkeypatch,
):
    configure_google_settings(
        monkeypatch
    )

    profile = make_google_profile()

    await mock_google_authentication(
        monkeypatch,
        profile,
    )

    state = await get_google_state(
        client
    )

    response = await client.get(
        "/api/v1/auth/oauth/google/callback",
        params={
            "code": "test-code",
            "state": state,
        },
        headers={
            "User-Agent": "WorkforceOS-Google-Test/1.0",
            "X-Device-Name": "Google OAuth Test Device",
        },
    )

    assert response.status_code == 200, response.text

    result = await db_session.execute(
        select(RefreshSession).order_by(
            RefreshSession.created_at.desc()
        )
    )

    session = result.scalars().first()

    assert session is not None

    assert (
        session.user_agent
        == "WorkforceOS-Google-Test/1.0"
    )

    assert (
        session.device_name
        == "Google OAuth Test Device"
    )