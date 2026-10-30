from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

import httpx


# =========================================================
# GOOGLE OPENID CONNECT ENDPOINTS
# =========================================================


GOOGLE_AUTHORIZATION_ENDPOINT = (
    "https://accounts.google.com/o/oauth2/v2/auth"
)

GOOGLE_TOKEN_ENDPOINT = (
    "https://oauth2.googleapis.com/token"
)

GOOGLE_USERINFO_ENDPOINT = (
    "https://openidconnect.googleapis.com/v1/userinfo"
)

GOOGLE_ISSUERS = {
    "https://accounts.google.com",
    "accounts.google.com",
}

DEFAULT_GOOGLE_SCOPES = (
    "openid",
    "email",
    "profile",
)

DEFAULT_STATE_TTL_SECONDS = 600
DEFAULT_HTTP_TIMEOUT_SECONDS = 15.0


# =========================================================
# EXCEPTIONS
# =========================================================


class GoogleOAuthError(Exception):
    """
    Base exception for Google OAuth failures.

    This exception intentionally contains only safe application-facing
    information. Provider tokens, client secrets and raw responses must
    never be included in the message.
    """

    def __init__(
        self,
        message: str,
        *,
        code: str = "GOOGLE_OAUTH_ERROR",
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class GoogleOAuthConfigurationError(
    GoogleOAuthError
):
    pass


class GoogleOAuthStateError(
    GoogleOAuthError
):
    pass


class GoogleOAuthProviderError(
    GoogleOAuthError
):
    pass


class GoogleOAuthProfileError(
    GoogleOAuthError
):
    pass


# =========================================================
# DATA OBJECTS
# =========================================================


@dataclass(frozen=True, slots=True)
class GoogleOAuthState:
    value: str
    nonce: str
    expires_at: int
    intent: str
    remember_me: bool


@dataclass(frozen=True, slots=True)
class GooglePKCEPair:
    code_verifier: str
    code_challenge: str


@dataclass(frozen=True, slots=True)
class GoogleTokenSet:
    access_token: str
    token_type: str
    expires_in: int | None
    scope: str | None
    id_token: str | None
    refresh_token: str | None

    def __repr__(self) -> str:
        return (
            "GoogleTokenSet("
            "access_token=<redacted>, "
            f"token_type={self.token_type!r}, "
            f"expires_in={self.expires_in!r}, "
            f"scope={self.scope!r}, "
            "id_token="
            f"{'<redacted>' if self.id_token else None}, "
            "refresh_token="
            f"{'<redacted>' if self.refresh_token else None}"
            ")"
        )


@dataclass(frozen=True, slots=True)
class GoogleUserProfile:
    """
    Normalized Google identity information.

    `provider_user_id` is Google's immutable OpenID Connect `sub`
    identifier and should be used as the provider identity key.

    Email must NOT be used as Google's provider identity key.
    """

    provider: str
    provider_user_id: str
    email: str
    email_verified: bool
    first_name: str | None
    last_name: str | None
    display_name: str | None
    avatar_url: str | None
    locale: str | None

    @property
    def subject(self) -> str:
        return self.provider_user_id


# =========================================================
# INTERNAL HELPERS
# =========================================================


def _require_non_empty(
    value: str | None,
    *,
    field_name: str,
) -> str:
    if value is None:
        raise GoogleOAuthConfigurationError(
            f"{field_name} is not configured.",
            code="GOOGLE_OAUTH_NOT_CONFIGURED",
        )

    normalized = value.strip()

    if not normalized:
        raise GoogleOAuthConfigurationError(
            f"{field_name} is not configured.",
            code="GOOGLE_OAUTH_NOT_CONFIGURED",
        )

    return normalized


def _urlsafe_b64encode(
    value: bytes,
) -> str:
    return (
        base64.urlsafe_b64encode(value)
        .rstrip(b"=")
        .decode("ascii")
    )


def _urlsafe_b64decode(
    value: str,
) -> bytes:
    padding = "=" * (-len(value) % 4)

    try:
        return base64.urlsafe_b64decode(
            value + padding
        )
    except Exception as exc:
        raise GoogleOAuthStateError(
            "Invalid OAuth state.",
            code="INVALID_OAUTH_STATE",
        ) from exc


def _sign_state_payload(
    encoded_payload: str,
    *,
    state_secret: str,
) -> str:
    secret = _require_non_empty(
        state_secret,
        field_name="OAuth state secret",
    )

    signature = hmac.new(
        secret.encode("utf-8"),
        encoded_payload.encode("ascii"),
        hashlib.sha256,
    ).digest()

    return _urlsafe_b64encode(signature)


def _safe_json_object(
    response: httpx.Response,
) -> dict[str, Any]:
    try:
        data = response.json()
    except (
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        raise GoogleOAuthProviderError(
            "Google returned an invalid response.",
            code="GOOGLE_PROVIDER_INVALID_RESPONSE",
        ) from exc

    if not isinstance(data, dict):
        raise GoogleOAuthProviderError(
            "Google returned an invalid response.",
            code="GOOGLE_PROVIDER_INVALID_RESPONSE",
        )

    return data


def _provider_error_code(
    data: dict[str, Any],
) -> str | None:
    raw_error = data.get("error")

    if isinstance(raw_error, str):
        return raw_error[:100]

    if isinstance(raw_error, dict):
        code = raw_error.get("status")

        if isinstance(code, str):
            return code[:100]

    return None


# =========================================================
# STATE / CSRF PROTECTION
# =========================================================


def create_google_oauth_state(
    *,
    state_secret: str,
    intent: str,
    remember_me: bool = False,
    ttl_seconds: int = DEFAULT_STATE_TTL_SECONDS,
    now: int | None = None,
) -> GoogleOAuthState:
    """
    Create an HMAC-protected, time-limited OAuth state token.

    The signed state protects the authorization callback against login
    CSRF and carries the trusted WorkforceOS authentication intent.

    No client secret, OAuth token, password, or other credential is
    embedded in the state.
    """

    if ttl_seconds <= 0:
        raise ValueError(
            "ttl_seconds must be greater than zero."
        )

    normalized_intent = (
        intent.strip().lower()
    )

    if normalized_intent not in {
        "login",
        "signup",
    }:
        raise GoogleOAuthStateError(
            "Invalid OAuth authentication intent.",
            code="INVALID_OAUTH_INTENT",
        )

    issued_at = (
        int(time.time())
        if now is None
        else int(now)
    )

    expires_at = (
        issued_at +
        ttl_seconds
    )

    nonce = secrets.token_urlsafe(
        32
    )

    payload = {
        "nonce": nonce,
        "iat": issued_at,
        "exp": expires_at,
        "intent": normalized_intent,
        "remember_me": bool(
            remember_me
        ),
    }

    serialized = json.dumps(
        payload,
        separators=(",", ":"),
        sort_keys=True,
    ).encode(
        "utf-8"
    )

    encoded_payload = (
        _urlsafe_b64encode(
            serialized
        )
    )

    signature = (
        _sign_state_payload(
            encoded_payload,
            state_secret=
                state_secret,
        )
    )

    return GoogleOAuthState(
        value=(
            f"{encoded_payload}."
            f"{signature}"
        ),
        nonce=nonce,
        expires_at=
            expires_at,
        intent=
            normalized_intent,
        remember_me=
            bool(
                remember_me
            ),
    )


def verify_google_oauth_state(
    state: str,
    *,
    state_secret: str,
    now: int | None = None,
) -> dict[str, Any]:
    """
    Validate state integrity and expiry.

    Returns the verified state payload.

    State verification must occur before exchanging an authorization
    code received through the callback.
    """

    if not state or not state.strip():
        raise GoogleOAuthStateError(
            "OAuth state is required.",
            code="MISSING_OAUTH_STATE",
        )

    parts = state.split(".")

    if len(parts) != 2:
        raise GoogleOAuthStateError(
            "Invalid OAuth state.",
            code="INVALID_OAUTH_STATE",
        )

    encoded_payload, received_signature = (
        parts
    )

    expected_signature = (
        _sign_state_payload(
            encoded_payload,
            state_secret=
                state_secret,
        )
    )

    if not hmac.compare_digest(
        received_signature,
        expected_signature,
    ):
        raise GoogleOAuthStateError(
            "Invalid OAuth state.",
            code="INVALID_OAUTH_STATE",
        )

    raw_payload = (
        _urlsafe_b64decode(
            encoded_payload
        )
    )

    try:
        payload = json.loads(
            raw_payload.decode(
                "utf-8"
            )
        )

    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
    ) as exc:
        raise GoogleOAuthStateError(
            "Invalid OAuth state.",
            code="INVALID_OAUTH_STATE",
        ) from exc

    if not isinstance(
        payload,
        dict,
    ):
        raise GoogleOAuthStateError(
            "Invalid OAuth state.",
            code="INVALID_OAUTH_STATE",
        )

    nonce = payload.get(
        "nonce"
    )

    issued_at = payload.get(
        "iat"
    )

    expires_at = payload.get(
        "exp"
    )

    if (
        not isinstance(
            nonce,
            str,
        )
        or not nonce
        or not isinstance(
            issued_at,
            int,
        )
        or not isinstance(
            expires_at,
            int,
        )
    ):
        raise GoogleOAuthStateError(
            "Invalid OAuth state.",
            code="INVALID_OAUTH_STATE",
        )

    current_time = (
        int(time.time())
        if now is None
        else int(now)
    )

    if expires_at <= current_time:
        raise GoogleOAuthStateError(
            "OAuth state has expired.",
            code="OAUTH_STATE_EXPIRED",
        )

    if (
        issued_at >
        current_time + 60
    ):
        raise GoogleOAuthStateError(
            "Invalid OAuth state.",
            code="INVALID_OAUTH_STATE",
        )

    if expires_at <= issued_at:
        raise GoogleOAuthStateError(
            "Invalid OAuth state.",
            code="INVALID_OAUTH_STATE",
        )

    intent = payload.get(
        "intent"
    )

    remember_me = payload.get(
        "remember_me"
    )

    if intent not in {
        "login",
        "signup",
    }:
        raise GoogleOAuthStateError(
            "Invalid OAuth authentication intent.",
            code="INVALID_OAUTH_INTENT",
        )

    if not isinstance(
        remember_me,
        bool,
    ):
        raise GoogleOAuthStateError(
            "Invalid OAuth persistence preference.",
            code="INVALID_OAUTH_STATE",
        )

    return payload


# =========================================================
# PKCE
# =========================================================


def create_google_pkce_pair() -> GooglePKCEPair:
    """
    Generate an RFC 7636 S256 PKCE verifier/challenge pair.

    The caller must retain the verifier securely until the callback.
    Only the challenge is sent to Google's authorization endpoint.
    """

    code_verifier = (
        secrets.token_urlsafe(
            64
        )
    )

    digest = hashlib.sha256(
        code_verifier.encode(
            "ascii"
        )
    ).digest()

    code_challenge = (
        _urlsafe_b64encode(
            digest
        )
    )

    return GooglePKCEPair(
        code_verifier=
            code_verifier,
        code_challenge=
            code_challenge,
    )


# =========================================================
# AUTHORIZATION URL
# =========================================================


def build_google_authorization_url(
    *,
    client_id: str,
    redirect_uri: str,
    state: str,
    scopes: tuple[str, ...] = DEFAULT_GOOGLE_SCOPES,
    code_challenge: str | None = None,
    prompt: str | None = "select_account",
    login_hint: str | None = None,
) -> str:
    """
    Build the server-side Google OAuth/OpenID Connect authorization URL.

    The caller should redirect the browser to the returned URL.
    """

    normalized_client_id = (
        _require_non_empty(
            client_id,
            field_name=
                "Google OAuth client ID",
        )
    )

    normalized_redirect_uri = (
        _require_non_empty(
            redirect_uri,
            field_name=
                "Google OAuth redirect URI",
        )
    )

    if not state or not state.strip():
        raise GoogleOAuthStateError(
            "OAuth state is required.",
            code="MISSING_OAUTH_STATE",
        )

    cleaned_scopes = tuple(
        scope.strip()
        for scope in scopes
        if scope and scope.strip()
    )

    if not cleaned_scopes:
        raise GoogleOAuthConfigurationError(
            "At least one Google OAuth scope is required.",
            code="GOOGLE_OAUTH_INVALID_SCOPES",
        )

    params: dict[str, str] = {
        "client_id":
            normalized_client_id,
        "redirect_uri":
            normalized_redirect_uri,
        "response_type":
            "code",
        "scope":
            " ".join(
                cleaned_scopes
            ),
        "state":
            state,
        "include_granted_scopes":
            "true",
    }

    if prompt:
        params["prompt"] = (
            prompt.strip()
        )

    if login_hint:
        params["login_hint"] = (
            login_hint.strip()
        )

    if code_challenge:
        params[
            "code_challenge"
        ] = (
            code_challenge.strip()
        )

        params[
            "code_challenge_method"
        ] = "S256"

    return (
        f"{GOOGLE_AUTHORIZATION_ENDPOINT}"
        f"?{urlencode(params)}"
    )


# =========================================================
# AUTHORIZATION CODE EXCHANGE
# =========================================================


async def exchange_google_authorization_code(
    *,
    code: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    code_verifier: str | None = None,
    http_client: httpx.AsyncClient | None = None,
    timeout_seconds: float = DEFAULT_HTTP_TIMEOUT_SECONDS,
) -> GoogleTokenSet:
    """
    Exchange a one-time Google authorization code for provider tokens.

    Provider tokens are returned only to the calling auth service.
    They must never be logged or returned to the WorkforceOS frontend.
    """

    normalized_code = (
        _require_non_empty(
            code,
            field_name=
                "Google authorization code",
        )
    )

    normalized_client_id = (
        _require_non_empty(
            client_id,
            field_name=
                "Google OAuth client ID",
        )
    )

    normalized_client_secret = (
        _require_non_empty(
            client_secret,
            field_name=
                "Google OAuth client secret",
        )
    )

    normalized_redirect_uri = (
        _require_non_empty(
            redirect_uri,
            field_name=
                "Google OAuth redirect URI",
        )
    )

    payload: dict[
        str,
        str,
    ] = {
        "code":
            normalized_code,
        "client_id":
            normalized_client_id,
        "client_secret":
            normalized_client_secret,
        "redirect_uri":
            normalized_redirect_uri,
        "grant_type":
            "authorization_code",
    }

    if code_verifier:
        payload[
            "code_verifier"
        ] = (
            code_verifier.strip()
        )

    owns_client = (
        http_client is None
    )

    client = (
        httpx.AsyncClient(
            timeout=
                timeout_seconds
        )
        if http_client is None
        else http_client
    )

    try:
        try:
            response = await client.post(
                GOOGLE_TOKEN_ENDPOINT,
                data=payload,
                headers={
                    "Accept":
                        "application/json",
                },
            )

        except httpx.TimeoutException as exc:
            raise GoogleOAuthProviderError(
                "Google authentication timed out.",
                code=
                    "GOOGLE_PROVIDER_TIMEOUT",
            ) from exc

        except httpx.HTTPError as exc:
            raise GoogleOAuthProviderError(
                "Google authentication is temporarily unavailable.",
                code=
                    "GOOGLE_PROVIDER_UNAVAILABLE",
            ) from exc

        data = _safe_json_object(
            response
        )

        if response.status_code != 200:
            provider_code = (
                _provider_error_code(
                    data
                )
            )

            if (
                provider_code ==
                "invalid_grant"
            ):
                safe_code = (
                    "GOOGLE_INVALID_AUTHORIZATION_CODE"
                )
            else:
                safe_code = (
                    "GOOGLE_TOKEN_EXCHANGE_FAILED"
                )

            raise GoogleOAuthProviderError(
                "Google authorization could not be completed.",
                code=safe_code,
            )

        access_token = data.get(
            "access_token"
        )

        token_type = data.get(
            "token_type"
        )

        if (
            not isinstance(
                access_token,
                str,
            )
            or not access_token
            or not isinstance(
                token_type,
                str,
            )
            or not token_type
        ):
            raise GoogleOAuthProviderError(
                "Google returned an incomplete token response.",
                code=
                    "GOOGLE_PROVIDER_INVALID_RESPONSE",
            )

        expires_in_raw = data.get(
            "expires_in"
        )

        expires_in: int | None = (
            None
        )

        if isinstance(
            expires_in_raw,
            int,
        ):
            expires_in = (
                expires_in_raw
            )

        elif isinstance(
            expires_in_raw,
            str,
        ):
            try:
                expires_in = int(
                    expires_in_raw
                )
            except ValueError:
                expires_in = None

        scope = data.get(
            "scope"
        )

        id_token = data.get(
            "id_token"
        )

        refresh_token = data.get(
            "refresh_token"
        )

        return GoogleTokenSet(
            access_token=
                access_token,
            token_type=
                token_type,
            expires_in=
                expires_in,
            scope=(
                scope
                if isinstance(
                    scope,
                    str,
                )
                else None
            ),
            id_token=(
                id_token
                if isinstance(
                    id_token,
                    str,
                )
                else None
            ),
            refresh_token=(
                refresh_token
                if isinstance(
                    refresh_token,
                    str,
                )
                else None
            ),
        )

    finally:
        if owns_client:
            await client.aclose()


# =========================================================
# USERINFO
# =========================================================


async def fetch_google_user_profile(
    *,
    access_token: str,
    http_client: httpx.AsyncClient | None = None,
    timeout_seconds: float = DEFAULT_HTTP_TIMEOUT_SECONDS,
) -> GoogleUserProfile:
    """
    Fetch and normalize the authenticated Google user's OIDC profile.

    Security requirements:
    - Google `sub` is the immutable provider identity key.
    - email must be present.
    - email must be verified.
    - access token is never logged.
    """

    normalized_access_token = (
        _require_non_empty(
            access_token,
            field_name=
                "Google access token",
        )
    )

    owns_client = (
        http_client is None
    )

    client = (
        httpx.AsyncClient(
            timeout=
                timeout_seconds
        )
        if http_client is None
        else http_client
    )

    try:
        try:
            response = await client.get(
                GOOGLE_USERINFO_ENDPOINT,
                headers={
                    "Authorization": (
                        f"Bearer "
                        f"{normalized_access_token}"
                    ),
                    "Accept":
                        "application/json",
                },
            )

        except httpx.TimeoutException as exc:
            raise GoogleOAuthProviderError(
                "Google authentication timed out.",
                code=
                    "GOOGLE_PROVIDER_TIMEOUT",
            ) from exc

        except httpx.HTTPError as exc:
            raise GoogleOAuthProviderError(
                "Google authentication is temporarily unavailable.",
                code=
                    "GOOGLE_PROVIDER_UNAVAILABLE",
            ) from exc

        data = _safe_json_object(
            response
        )

        if response.status_code != 200:
            raise GoogleOAuthProviderError(
                "Google profile could not be retrieved.",
                code=
                    "GOOGLE_USERINFO_FAILED",
            )

        subject = data.get(
            "sub"
        )

        email = data.get(
            "email"
        )

        email_verified = data.get(
            "email_verified"
        )

        if (
            not isinstance(
                subject,
                str,
            )
            or not subject.strip()
        ):
            raise GoogleOAuthProfileError(
                "Google profile is missing its subject identifier.",
                code=
                    "GOOGLE_PROFILE_INVALID",
            )

        if (
            not isinstance(
                email,
                str,
            )
            or not email.strip()
        ):
            raise GoogleOAuthProfileError(
                "Google account does not provide an email address.",
                code=
                    "GOOGLE_EMAIL_REQUIRED",
            )

        if email_verified is not True:
            raise GoogleOAuthProfileError(
                "Google account email is not verified.",
                code=
                    "GOOGLE_EMAIL_NOT_VERIFIED",
            )

        normalized_email = (
            email
            .strip()
            .lower()
        )

        given_name = data.get(
            "given_name"
        )

        family_name = data.get(
            "family_name"
        )

        display_name = data.get(
            "name"
        )

        picture = data.get(
            "picture"
        )

        locale = data.get(
            "locale"
        )

        return GoogleUserProfile(
            provider=
                "google",
            provider_user_id=
                subject.strip(),
            email=
                normalized_email,
            email_verified=
                True,
            first_name=(
                given_name.strip()
                if isinstance(
                    given_name,
                    str,
                )
                and given_name.strip()
                else None
            ),
            last_name=(
                family_name.strip()
                if isinstance(
                    family_name,
                    str,
                )
                and family_name.strip()
                else None
            ),
            display_name=(
                display_name.strip()
                if isinstance(
                    display_name,
                    str,
                )
                and display_name.strip()
                else None
            ),
            avatar_url=(
                picture.strip()
                if isinstance(
                    picture,
                    str,
                )
                and picture.strip()
                else None
            ),
            locale=(
                locale.strip()
                if isinstance(
                    locale,
                    str,
                )
                and locale.strip()
                else None
            ),
        )

    finally:
        if owns_client:
            await client.aclose()


# =========================================================
# COMPLETE PROVIDER FLOW
# =========================================================


async def authenticate_google_authorization_code(
    *,
    code: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    code_verifier: str | None = None,
    http_client: httpx.AsyncClient | None = None,
    timeout_seconds: float = DEFAULT_HTTP_TIMEOUT_SECONDS,
) -> tuple[
    GoogleUserProfile,
    GoogleTokenSet,
]:
    """
    Exchange an authorization code and retrieve the Google profile.

    This function performs PROVIDER authentication only.
    """

    if http_client is not None:
        token_set = (
            await exchange_google_authorization_code(
                code=
                    code,
                client_id=
                    client_id,
                client_secret=
                    client_secret,
                redirect_uri=
                    redirect_uri,
                code_verifier=
                    code_verifier,
                http_client=
                    http_client,
                timeout_seconds=
                    timeout_seconds,
            )
        )

        profile = (
            await fetch_google_user_profile(
                access_token=
                    token_set.access_token,
                http_client=
                    http_client,
                timeout_seconds=
                    timeout_seconds,
            )
        )

        return (
            profile,
            token_set,
        )

    async with httpx.AsyncClient(
        timeout=
            timeout_seconds
    ) as client:
        token_set = (
            await exchange_google_authorization_code(
                code=
                    code,
                client_id=
                    client_id,
                client_secret=
                    client_secret,
                redirect_uri=
                    redirect_uri,
                code_verifier=
                    code_verifier,
                http_client=
                    client,
                timeout_seconds=
                    timeout_seconds,
            )
        )

        profile = (
            await fetch_google_user_profile(
                access_token=
                    token_set.access_token,
                http_client=
                    client,
                timeout_seconds=
                    timeout_seconds,
            )
        )

        return (
            profile,
            token_set,
        )