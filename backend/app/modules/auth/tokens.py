from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from app.config import settings
from app.core.exceptions import InvalidToken, TokenExpired
from app.core.security import (
    create_access_token as core_create_access_token,
    create_refresh_token as core_create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    generate_security_id,
    hash_token,
)


# =========================================================
# TOKEN / SESSION DATA
# =========================================================


@dataclass(slots=True)
class TokenPairData:
    """
    Internal representation of an issued WorkforceOS token pair.

    This is a domain object, not an API response schema.

    The API layer will later map this into TokenResponse.
    """

    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int

    access_jti: str
    refresh_jti: str

    session_id: uuid.UUID

    access_expires_at: datetime
    refresh_expires_at: datetime


@dataclass(slots=True)
class RefreshTokenClaims:
    """
    Normalized refresh-token claims.

    Used by the service/repository layer when validating
    a refresh session.
    """

    user_id: uuid.UUID
    session_id: uuid.UUID
    jti: str
    issued_at: datetime
    expires_at: datetime


@dataclass(slots=True)
class AccessTokenClaims:
    """
    Normalized access-token claims.

    Access token confirms global WorkforceOS identity.

    Workspace membership and RBAC must still be checked
    separately later.
    """

    user_id: uuid.UUID
    session_id: uuid.UUID
    jti: str
    issued_at: datetime
    expires_at: datetime


# =========================================================
# TIME HELPERS
# =========================================================


def utc_now() -> datetime:
    """
    Return current timezone-aware UTC datetime.
    """

    return datetime.now(timezone.utc)


def access_token_expiry() -> datetime:
    """
    Calculate access-token expiration.
    """

    return utc_now() + timedelta(
        minutes=settings.access_token_minutes
    )


def refresh_token_expiry() -> datetime:
    """
    Calculate refresh-token expiration.
    """

    return utc_now() + timedelta(
        days=settings.refresh_token_days
    )


# =========================================================
# SESSION ID
# =========================================================


def generate_session_id() -> uuid.UUID:
    """
    Generate the server-side authentication session ID.

    One session normally represents one logged-in browser/device.

    Example:

        User
          ├── Chrome / Windows
          ├── Mobile
          └── Desktop app

    Each can have a separate refresh session.
    """

    return uuid.uuid4()


# =========================================================
# ACCESS TOKEN CREATION
# =========================================================


def create_access_token(
    *,
    user_id: uuid.UUID | str,
    session_id: uuid.UUID | str,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """
    Create an access JWT for an authenticated WorkforceOS user.

    Built-in custom claims:

        session_id

    Important:
    Do NOT put authoritative workspace permissions into this token.

    Later workflow:

        JWT identity
            ↓
        authenticated user
            ↓
        workspace membership lookup
            ↓
        RBAC lookup
            ↓
        tenant routing
    """

    claims: dict[str, Any] = {
        "session_id": str(
            session_id
        ),
    }

    if extra_claims:
        claims.update(
            extra_claims
        )

    return core_create_access_token(
        subject=str(user_id),
        extra=claims,
    )


# =========================================================
# REFRESH TOKEN CREATION
# =========================================================


def create_refresh_token(
    *,
    user_id: uuid.UUID | str,
    session_id: uuid.UUID | str,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """
    Create a refresh JWT linked to one server-side session.

    The raw refresh token is returned to the authenticated client.

    The database should store:

        token_hash

    NOT the raw refresh token.
    """

    claims: dict[str, Any] = {
        "session_id": str(
            session_id
        ),
    }

    if extra_claims:
        claims.update(
            extra_claims
        )

    return core_create_refresh_token(
        subject=str(user_id),
        extra=claims,
    )


# =========================================================
# TOKEN PAIR
# =========================================================


def create_token_pair(
    *,
    user_id: uuid.UUID | str,
    session_id: uuid.UUID | None = None,
    access_extra_claims: dict[str, Any] | None = None,
    refresh_extra_claims: dict[str, Any] | None = None,
) -> TokenPairData:
    """
    Generate a complete WorkforceOS access/refresh pair.

    If session_id is omitted, a new one is generated.

    This function does not persist the refresh session.
    Persistence belongs to auth/repository.py + auth/service.py.
    """

    resolved_session_id = (
        session_id
        or generate_session_id()
    )

    access_token = create_access_token(
        user_id=user_id,
        session_id=resolved_session_id,
        extra_claims=access_extra_claims,
    )

    refresh_token = create_refresh_token(
        user_id=user_id,
        session_id=resolved_session_id,
        extra_claims=refresh_extra_claims,
    )

    access_payload = decode_access_token(
        access_token
    )

    refresh_payload = decode_refresh_token(
        refresh_token
    )

    return TokenPairData(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=(
            settings.access_token_minutes
            * 60
        ),
        access_jti=str(
            access_payload["jti"]
        ),
        refresh_jti=str(
            refresh_payload["jti"]
        ),
        session_id=resolved_session_id,
        access_expires_at=_timestamp_to_datetime(
            access_payload["exp"]
        ),
        refresh_expires_at=_timestamp_to_datetime(
            refresh_payload["exp"]
        ),
    )


# =========================================================
# REFRESH TOKEN HASH
# =========================================================


def create_refresh_token_hash(
    refresh_token: str,
) -> str:
    """
    Generate the hash persisted in refresh_sessions.token_hash.

    Database:

        refresh_sessions
            token_hash = HMAC(raw_refresh_token)

    Client:

        receives raw refresh token

    If the database is leaked, raw refresh tokens are not
    directly exposed.
    """

    if not refresh_token:
        raise ValueError(
            "Refresh token cannot be empty."
        )

    return hash_token(
        refresh_token
    )


# =========================================================
# ACCESS TOKEN CLAIMS
# =========================================================


def parse_access_token(
    token: str,
) -> AccessTokenClaims:
    """
    Decode and normalize an access token.

    Raises:
        InvalidToken
        TokenExpired
    """

    payload = decode_access_token(
        token
    )

    user_id = _parse_uuid_claim(
        payload,
        "sub",
        "Access token user ID is invalid.",
    )

    session_id = _parse_uuid_claim(
        payload,
        "session_id",
        "Access token session ID is invalid.",
    )

    jti = _require_string_claim(
        payload,
        "jti",
        "Access token identifier is invalid.",
    )

    issued_at = _timestamp_to_datetime(
        payload.get("iat")
    )

    expires_at = _timestamp_to_datetime(
        payload.get("exp")
    )

    return AccessTokenClaims(
        user_id=user_id,
        session_id=session_id,
        jti=jti,
        issued_at=issued_at,
        expires_at=expires_at,
    )


# =========================================================
# REFRESH TOKEN CLAIMS
# =========================================================


def parse_refresh_token(
    token: str,
) -> RefreshTokenClaims:
    """
    Decode and normalize a refresh token.

    Raises:
        InvalidToken
        TokenExpired
    """

    payload = decode_refresh_token(
        token
    )

    user_id = _parse_uuid_claim(
        payload,
        "sub",
        "Refresh token user ID is invalid.",
    )

    session_id = _parse_uuid_claim(
        payload,
        "session_id",
        "Refresh token session ID is invalid.",
    )

    jti = _require_string_claim(
        payload,
        "jti",
        "Refresh token identifier is invalid.",
    )

    issued_at = _timestamp_to_datetime(
        payload.get("iat")
    )

    expires_at = _timestamp_to_datetime(
        payload.get("exp")
    )

    return RefreshTokenClaims(
        user_id=user_id,
        session_id=session_id,
        jti=jti,
        issued_at=issued_at,
        expires_at=expires_at,
    )


# =========================================================
# REFRESH TOKEN BASIC VALIDATION
# =========================================================


def validate_refresh_token(
    token: str,
) -> RefreshTokenClaims:
    """
    Perform cryptographic/claim validation for a refresh token.

    IMPORTANT:
    This does NOT prove the session is still valid.

    auth/service.py must later additionally check:

        session exists
        session.user_id matches token
        session.jti matches token
        token hash matches DB
        session not revoked
        session not expired
        session not already rotated/reused
    """

    claims = parse_refresh_token(
        token
    )

    if claims.expires_at <= utc_now():
        raise TokenExpired(
            "Refresh token has expired."
        )

    return claims


# =========================================================
# ACCESS TOKEN BASIC VALIDATION
# =========================================================


def validate_access_token(
    token: str,
) -> AccessTokenClaims:
    """
    Validate and normalize an access token.

    Workspace authorization is intentionally NOT performed here.
    """

    claims = parse_access_token(
        token
    )

    if claims.expires_at <= utc_now():
        raise TokenExpired(
            "Access token has expired."
        )

    return claims


# =========================================================
# ROTATION
# =========================================================


def rotate_token_pair(
    *,
    user_id: uuid.UUID | str,
    session_id: uuid.UUID,
) -> TokenPairData:
    """
    Generate the replacement token pair during refresh rotation.

    Database orchestration is intentionally outside this function.

    Correct service flow later:

        receive old refresh token
            ↓
        decode token
            ↓
        find DB session
            ↓
        compare token hash
            ↓
        validate session state
            ↓
        generate replacement pair
            ↓
        revoke/rotate old DB session
            ↓
        create replacement DB session
            ↓
        commit transaction
            ↓
        return new tokens
    """

    return create_token_pair(
        user_id=user_id,
        session_id=session_id,
    )


# =========================================================
# TOKEN EXPIRY HELPERS
# =========================================================


def seconds_until_expiry(
    expires_at: datetime,
) -> int:
    """
    Return remaining seconds until a token/session expires.

    Never returns a negative number.
    """

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(
            tzinfo=timezone.utc
        )

    remaining = (
        expires_at
        - utc_now()
    ).total_seconds()

    return max(
        0,
        int(remaining),
    )


def is_expired(
    expires_at: datetime,
) -> bool:
    """
    Return True when a timestamp is expired.
    """

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(
            tzinfo=timezone.utc
        )

    return expires_at <= utc_now()


# =========================================================
# INTERNAL HELPERS
# =========================================================


def _parse_uuid_claim(
    payload: dict[str, Any],
    key: str,
    error_message: str,
) -> uuid.UUID:
    value = payload.get(
        key
    )

    if value is None:
        raise InvalidToken(
            error_message
        )

    try:
        return uuid.UUID(
            str(value)
        )

    except (
        TypeError,
        ValueError,
        AttributeError,
    ) as exc:
        raise InvalidToken(
            error_message
        ) from exc


def _require_string_claim(
    payload: dict[str, Any],
    key: str,
    error_message: str,
) -> str:
    value = payload.get(
        key
    )

    if not isinstance(
        value,
        str,
    ) or not value:
        raise InvalidToken(
            error_message
        )

    return value


def _timestamp_to_datetime(
    value: Any,
) -> datetime:
    """
    Convert a JWT NumericDate claim to UTC datetime.

    PyJWT normally returns iat/exp as integer timestamps after decode.
    """

    if isinstance(
        value,
        datetime,
    ):
        if value.tzinfo is None:
            return value.replace(
                tzinfo=timezone.utc
            )

        return value.astimezone(
            timezone.utc
        )

    if isinstance(
        value,
        (int, float),
    ):
        return datetime.fromtimestamp(
            value,
            tz=timezone.utc,
        )

    raise InvalidToken(
        "Authentication token timestamp is invalid."
    )


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "TokenPairData",
    "AccessTokenClaims",
    "RefreshTokenClaims",
    "utc_now",
    "access_token_expiry",
    "refresh_token_expiry",
    "generate_session_id",
    "create_access_token",
    "create_refresh_token",
    "create_token_pair",
    "create_refresh_token_hash",
    "parse_access_token",
    "parse_refresh_token",
    "validate_access_token",
    "validate_refresh_token",
    "rotate_token_pair",
    "seconds_until_expiry",
    "is_expired",
]