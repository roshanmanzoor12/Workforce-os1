from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import string
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

import jwt
from jwt.exceptions import (
    ExpiredSignatureError,
    InvalidTokenError as PyJWTInvalidTokenError,
)
from pwdlib import PasswordHash

from app.config import settings
from app.core.exceptions import (
    ConfigurationError,
    InvalidToken,
    TokenExpired,
)
from app.core.logging import get_logger


logger = get_logger(__name__)


# =========================================================
# TYPES
# =========================================================

TokenType = Literal[
    "access",
    "refresh",
]


# =========================================================
# CONSTANTS
# =========================================================

DEFAULT_RANDOM_TOKEN_BYTES = 32

MINIMUM_JWT_SECRET_LENGTH = 32

SUPPORTED_HMAC_ALGORITHMS = {
    "HS256",
    "HS384",
    "HS512",
}

RESERVED_JWT_CLAIMS = {
    "sub",
    "iat",
    "nbf",
    "exp",
    "jti",
    "type",
}


# =========================================================
# PASSWORD HASHER
# =========================================================

password_hash = PasswordHash.recommended()


# =========================================================
# TIME
# =========================================================

def utc_now() -> datetime:
    """
    Return the current UTC time as a timezone-aware datetime.
    """

    return datetime.now(timezone.utc)


# =========================================================
# SECURITY CONFIGURATION VALIDATION
# =========================================================

def validate_security_configuration() -> None:
    """
    Validate security-critical application settings.

    This should eventually be called during application startup.

    Raises:
        ConfigurationError
    """

    secret = settings.jwt_secret

    if not secret:
        raise ConfigurationError(
            "JWT_SECRET is not configured."
        )

    if len(secret) < MINIMUM_JWT_SECRET_LENGTH:
        raise ConfigurationError(
            "JWT_SECRET must contain at least "
            f"{MINIMUM_JWT_SECRET_LENGTH} characters."
        )

    if secret.startswith("CHANGE_THIS"):
        raise ConfigurationError(
            "JWT_SECRET is still using the development placeholder."
        )

    algorithm = settings.jwt_algorithm.upper()

    if algorithm not in SUPPORTED_HMAC_ALGORITHMS:
        raise ConfigurationError(
            f"Unsupported JWT algorithm: {algorithm}"
        )

    if settings.access_token_minutes <= 0:
        raise ConfigurationError(
            "ACCESS_TOKEN_MINUTES must be greater than 0."
        )

    if settings.refresh_token_days <= 0:
        raise ConfigurationError(
            "REFRESH_TOKEN_DAYS must be greater than 0."
        )

    if not 4 <= settings.otp_length <= 10:
        raise ConfigurationError(
            "OTP_LENGTH must be between 4 and 10."
        )


# =========================================================
# PASSWORD HASHING
# =========================================================

def hash_password(
    password: str,
) -> str:
    """
    Securely hash a password using pwdlib's recommended
    password hashing configuration.

    The plaintext password must never be stored in PostgreSQL,
    Redis, logs, or audit records.

    Returns:
        Encoded password hash.
    """

    if not isinstance(password, str):
        raise TypeError(
            "Password must be a string."
        )

    if not password:
        raise ValueError(
            "Password cannot be empty."
        )

    return password_hash.hash(
        password
    )


def verify_password(
    password: str,
    hashed_password: str,
) -> bool:
    """
    Safely verify a plaintext password against its stored hash.

    Returns False for malformed or invalid hashes instead of
    exposing password-hashing implementation details.
    """

    if not password:
        return False

    if not hashed_password:
        return False

    try:
        return bool(
            password_hash.verify(
                password,
                hashed_password,
            )
        )

    except Exception:
        logger.warning(
            "password_hash_verification_failed"
        )

        return False


# =========================================================
# SECURE RANDOM TOKENS
# =========================================================

def generate_secure_token(
    byte_length: int = DEFAULT_RANDOM_TOKEN_BYTES,
) -> str:
    """
    Generate a cryptographically secure URL-safe random token.

    Suitable for:
    - refresh-session identifiers
    - email verification links
    - password reset links
    - invitation tokens
    - API verification challenges

    Do not use random.random() for security tokens.
    """

    if byte_length < 16:
        raise ValueError(
            "Secure tokens must use at least 16 random bytes."
        )

    return secrets.token_urlsafe(
        byte_length
    )


def generate_security_id() -> str:
    """
    Generate a random UUID suitable for security identifiers.

    Common uses:
    - JWT jti
    - session IDs
    - challenge IDs
    """

    return str(
        uuid.uuid4()
    )


# =========================================================
# OTP
# =========================================================

def generate_otp(
    length: int | None = None,
) -> str:
    """
    Generate a cryptographically secure numeric OTP.

    Example with OTP_LENGTH=6:

        493182

    The returned OTP is meant to be delivered to the user.

    Do not persist the plaintext OTP in the database.
    Persist hash_otp(otp) instead.
    """

    otp_length = (
        length
        if length is not None
        else settings.otp_length
    )

    if not 4 <= otp_length <= 10:
        raise ValueError(
            "OTP length must be between 4 and 10."
        )

    return "".join(
        secrets.choice(
            string.digits
        )
        for _ in range(
            otp_length
        )
    )


# =========================================================
# HMAC HASHING
# =========================================================

def _security_hmac(
    value: str,
    *,
    namespace: str,
) -> str:
    """
    Generate an HMAC-SHA256 digest.

    Namespace separation ensures that an OTP hash and token hash
    cannot accidentally be treated as the same security primitive.
    """

    if not value:
        raise ValueError(
            "Security value cannot be empty."
        )

    message = (
        f"{namespace}:{value}"
    ).encode("utf-8")

    secret = settings.jwt_secret.encode(
        "utf-8"
    )

    return hmac.new(
        secret,
        message,
        hashlib.sha256,
    ).hexdigest()


def hash_otp(
    otp: str,
) -> str:
    """
    Produce the server-side hash that should be stored for an OTP.

    OTPs have low entropy, therefore keyed HMAC is preferred over
    storing a simple SHA-256 digest.
    """

    return _security_hmac(
        otp,
        namespace="otp",
    )


def verify_otp_hash(
    otp: str,
    stored_hash: str,
) -> bool:
    """
    Verify an OTP against its stored HMAC hash using
    constant-time comparison.
    """

    if not otp or not stored_hash:
        return False

    try:
        candidate_hash = hash_otp(
            otp
        )

        return secrets.compare_digest(
            candidate_hash,
            stored_hash,
        )

    except Exception:
        return False


def hash_token(
    token: str,
) -> str:
    """
    Create a one-way representation of a high-value token.

    Store the hash rather than the raw token when possible.

    Intended for:
    - refresh token records
    - email verification tokens
    - password reset tokens
    - invitation tokens
    """

    return _security_hmac(
        token,
        namespace="token",
    )


def verify_token_hash(
    token: str,
    stored_hash: str,
) -> bool:
    """
    Constant-time verification of a token against its stored hash.
    """

    if not token or not stored_hash:
        return False

    try:
        candidate_hash = hash_token(
            token
        )

        return secrets.compare_digest(
            candidate_hash,
            stored_hash,
        )

    except Exception:
        return False


# =========================================================
# CONSTANT-TIME COMPARISON
# =========================================================

def secure_compare(
    value_a: str,
    value_b: str,
) -> bool:
    """
    Perform constant-time string comparison.

    Useful for security-sensitive values where ordinary == may
    reveal timing differences.
    """

    if not isinstance(
        value_a,
        str,
    ):
        return False

    if not isinstance(
        value_b,
        str,
    ):
        return False

    return secrets.compare_digest(
        value_a,
        value_b,
    )


# =========================================================
# IDENTITY NORMALIZATION
# =========================================================

def normalize_email(
    email: str,
) -> str:
    """
    Normalize an email for consistent lookup and uniqueness.

    We intentionally do not perform provider-specific transformations
    such as removing Gmail dots or '+' aliases.
    """

    if not isinstance(
        email,
        str,
    ):
        raise TypeError(
            "Email must be a string."
        )

    return email.strip().lower()


def normalize_username(
    username: str,
) -> str:
    """
    Normalize a platform-wide username.

    Actual username policy validation will live in auth/schemas.py
    and auth/service.py.
    """

    if not isinstance(
        username,
        str,
    ):
        raise TypeError(
            "Username must be a string."
        )

    normalized = username.strip().lower()

    normalized = re.sub(
        r"\s+",
        "",
        normalized,
    )

    return normalized


# =========================================================
# JWT CLAIM HELPERS
# =========================================================

def _prepare_extra_claims(
    extra: dict[str, Any] | None,
) -> dict[str, Any]:
    """
    Validate custom JWT claims.

    Callers are not allowed to overwrite core security claims.
    """

    if not extra:
        return {}

    collision = (
        RESERVED_JWT_CLAIMS
        & set(extra.keys())
    )

    if collision:
        fields = ", ".join(
            sorted(collision)
        )

        raise ValueError(
            "Reserved JWT claims cannot be overwritten: "
            f"{fields}"
        )

    return dict(extra)


def _encode_token(
    *,
    subject: str,
    token_type: TokenType,
    expires_delta: timedelta,
    extra: dict[str, Any] | None = None,
) -> str:
    """
    Internal JWT creation function.

    All WorkforceOS access/refresh JWTs pass through this helper.
    """

    if not subject:
        raise ValueError(
            "Token subject cannot be empty."
        )

    now = utc_now()

    expires_at = (
        now
        + expires_delta
    )

    payload: dict[str, Any] = {
        "sub": str(subject),
        "iat": now,
        "nbf": now,
        "exp": expires_at,
        "jti": generate_security_id(),
        "type": token_type,
    }

    payload.update(
        _prepare_extra_claims(
            extra
        )
    )

    return jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


# =========================================================
# ACCESS TOKEN
# =========================================================

def create_access_token(
    subject: str,
    extra: dict[str, Any] | None = None,
) -> str:
    """
    Create a short-lived WorkforceOS access token.

    Typical JWT:

        {
            "sub": "user-uuid",
            "type": "access",
            "jti": "...",
            "iat": ...,
            "nbf": ...,
            "exp": ...
        }

    Additional safe claims may later include:

        platform_role
        session_id

    Workspace authorization should not blindly trust frontend claims.
    Membership must still be verified server-side.
    """

    return _encode_token(
        subject=subject,
        token_type="access",
        expires_delta=timedelta(
            minutes=settings.access_token_minutes
        ),
        extra=extra,
    )


# =========================================================
# REFRESH TOKEN
# =========================================================

def create_refresh_token(
    subject: str,
    extra: dict[str, Any] | None = None,
) -> str:
    """
    Create a longer-lived refresh token.

    Refresh tokens will later have corresponding server-side
    session records so they can be:

    - revoked
    - rotated
    - expired
    - invalidated on logout
    - invalidated on logout-all
    """

    return _encode_token(
        subject=subject,
        token_type="refresh",
        expires_delta=timedelta(
            days=settings.refresh_token_days
        ),
        extra=extra,
    )


# =========================================================
# TOKEN PAIR
# =========================================================

def create_token_pair(
    subject: str,
    *,
    access_extra: dict[str, Any] | None = None,
    refresh_extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Generate an access + refresh token pair.

    Returns:

        {
            "access_token": "...",
            "refresh_token": "...",
            "token_type": "bearer",
            "expires_in": 1800
        }
    """

    access_token = create_access_token(
        subject=subject,
        extra=access_extra,
    )

    refresh_token = create_refresh_token(
        subject=subject,
        extra=refresh_extra,
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": (
            settings.access_token_minutes
            * 60
        ),
    }


# =========================================================
# JWT DECODING
# =========================================================

def decode_token(
    token: str,
    *,
    expected_type: TokenType | None = None,
) -> dict[str, Any]:
    """
    Decode and validate a WorkforceOS JWT.

    Validation includes:

    - signature
    - expiration
    - required claims
    - token type when expected_type is supplied

    Raises:
        TokenExpired
        InvalidToken
    """

    if not token:
        raise InvalidToken(
            "Authentication token is missing."
        )

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[
                settings.jwt_algorithm
            ],
            options={
                "require": [
                    "sub",
                    "iat",
                    "nbf",
                    "exp",
                    "jti",
                    "type",
                ]
            },
        )

    except ExpiredSignatureError as exc:
        raise TokenExpired(
            "Authentication token has expired."
        ) from exc

    except PyJWTInvalidTokenError as exc:
        raise InvalidToken(
            "Authentication token is invalid."
        ) from exc

    token_type = payload.get(
        "type"
    )

    if token_type not in {
        "access",
        "refresh",
    }:
        raise InvalidToken(
            "Authentication token type is invalid."
        )

    if (
        expected_type is not None
        and token_type != expected_type
    ):
        raise InvalidToken(
            f"Expected a {expected_type} token."
        )

    subject = payload.get(
        "sub"
    )

    if not isinstance(
        subject,
        str,
    ) or not subject:
        raise InvalidToken(
            "Authentication token subject is invalid."
        )

    return payload


# =========================================================
# ACCESS / REFRESH DECODERS
# =========================================================

def decode_access_token(
    token: str,
) -> dict[str, Any]:
    """
    Decode a token and require type=access.
    """

    return decode_token(
        token,
        expected_type="access",
    )


def decode_refresh_token(
    token: str,
) -> dict[str, Any]:
    """
    Decode a token and require type=refresh.
    """

    return decode_token(
        token,
        expected_type="refresh",
    )


# =========================================================
# TOKEN CLAIM HELPERS
# =========================================================

def get_token_subject(
    token: str,
    *,
    expected_type: TokenType | None = None,
) -> str:
    """
    Decode a token and return its subject/user ID.
    """

    payload = decode_token(
        token,
        expected_type=expected_type,
    )

    return str(
        payload["sub"]
    )


def get_token_jti(
    token: str,
    *,
    expected_type: TokenType | None = None,
) -> str:
    """
    Decode a token and return its unique JWT ID.
    """

    payload = decode_token(
        token,
        expected_type=expected_type,
    )

    jti = payload.get(
        "jti"
    )

    if not isinstance(
        jti,
        str,
    ) or not jti:
        raise InvalidToken(
            "Authentication token identifier is invalid."
        )

    return jti


# =========================================================
# PUBLIC EXPORTS
# =========================================================

__all__ = [
    "TokenType",
    "utc_now",
    "validate_security_configuration",
    "hash_password",
    "verify_password",
    "generate_secure_token",
    "generate_security_id",
    "generate_otp",
    "hash_otp",
    "verify_otp_hash",
    "hash_token",
    "verify_token_hash",
    "secure_compare",
    "normalize_email",
    "normalize_username",
    "create_access_token",
    "create_refresh_token",
    "create_token_pair",
    "decode_token",
    "decode_access_token",
    "decode_refresh_token",
    "get_token_subject",
    "get_token_jti",
]