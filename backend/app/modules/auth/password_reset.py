from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.config import settings
from app.core.exceptions import (
    ResourceNotFound,
    ValidationError,
)
from app.core.security import (
    generate_otp,
    generate_secure_token,
    hash_otp,
    hash_token,
    verify_otp_hash,
    verify_token_hash,
)
from app.modules.auth.models import (
    PasswordResetChallenge,
    User,
)
from app.modules.auth.repository import AuthRepository


# =========================================================
# RESULT TYPES
# =========================================================


@dataclass(slots=True)
class PasswordResetIssueResult:
    """
    Result returned when a password-reset OTP challenge is created.

    otp is returned only to the service layer so it can be sent
    through the configured email provider.

    Plaintext OTP must never be stored in PostgreSQL.
    """

    challenge: PasswordResetChallenge
    otp: str
    expires_at: datetime


@dataclass(slots=True)
class PasswordResetVerificationResult:
    """
    Result returned after successful password-reset OTP verification.

    reset_token is a temporary high-entropy authorization token.

    Only its hash is persisted in the database.
    """

    challenge: PasswordResetChallenge
    reset_token: str
    reset_token_expires_at: datetime


@dataclass(slots=True)
class PasswordResetAuthorization:
    """
    Validated reset authorization.

    auth/service.py will use this result before changing the user's
    password.
    """

    challenge: PasswordResetChallenge
    user_id: object
    expires_at: datetime


# =========================================================
# TIME HELPERS
# =========================================================


def utc_now() -> datetime:
    """
    Return timezone-aware current UTC time.
    """

    return datetime.now(timezone.utc)


def get_password_reset_otp_expiry() -> datetime:
    """
    Calculate password-reset OTP expiration.
    """

    return utc_now() + timedelta(
        minutes=settings.password_reset_otp_minutes
    )


def get_reset_token_expiry() -> datetime:
    """
    Calculate temporary password reset authorization expiry.

    There is currently no dedicated reset-token TTL setting,
    so the OTP validity window is reused.

    A dedicated setting can be introduced later without changing
    the public flow.
    """

    return utc_now() + timedelta(
        minutes=settings.password_reset_otp_minutes
    )


# =========================================================
# DATETIME NORMALIZATION
# =========================================================


def _as_utc(
    value: datetime,
) -> datetime:
    """
    Normalize datetime to timezone-aware UTC.
    """

    if value.tzinfo is None:
        return value.replace(
            tzinfo=timezone.utc
        )

    return value.astimezone(
        timezone.utc
    )


# =========================================================
# CHALLENGE STATE HELPERS
# =========================================================


def is_challenge_expired(
    challenge: PasswordResetChallenge,
    *,
    now: datetime | None = None,
) -> bool:
    """
    Return True when reset OTP has expired.
    """

    current_time = now or utc_now()

    return (
        _as_utc(
            challenge.expires_at
        )
        <= current_time
    )


def is_challenge_consumed(
    challenge: PasswordResetChallenge,
) -> bool:
    """
    Return True after password reset has already been completed.
    """

    return (
        challenge.consumed_at
        is not None
    )


def is_challenge_invalidated(
    challenge: PasswordResetChallenge,
) -> bool:
    """
    Return True when challenge was explicitly invalidated.
    """

    return (
        challenge.invalidated_at
        is not None
    )


def attempts_exhausted(
    challenge: PasswordResetChallenge,
) -> bool:
    """
    Return True when maximum OTP attempts have been reached.
    """

    return (
        challenge.attempt_count
        >= challenge.max_attempts
    )


def is_challenge_verified(
    challenge: PasswordResetChallenge,
) -> bool:
    """
    Return True once OTP verification succeeded.
    """

    return (
        challenge.verified_at
        is not None
    )


def challenge_is_active(
    challenge: PasswordResetChallenge,
    *,
    now: datetime | None = None,
) -> bool:
    """
    Return True when the OTP challenge can still be used.
    """

    return (
        not is_challenge_expired(
            challenge,
            now=now,
        )
        and not is_challenge_consumed(
            challenge
        )
        and not is_challenge_invalidated(
            challenge
        )
        and not attempts_exhausted(
            challenge
        )
    )


# =========================================================
# ISSUE PASSWORD RESET
# =========================================================


async def issue_password_reset(
    *,
    repository: AuthRepository,
    user: User,
    requested_ip_address: str | None = None,
    requested_user_agent: str | None = None,
) -> PasswordResetIssueResult:
    """
    Create a fresh password-reset OTP challenge.

    Flow:

        forgot password
            ↓
        find global user
            ↓
        invalidate previous active reset challenges
            ↓
        generate secure OTP
            ↓
        HMAC-hash OTP
            ↓
        persist hash only
            ↓
        return plaintext OTP to service layer
            ↓
        service sends email

    Rate limiting belongs to auth/service.py using Redis.
    """

    now = utc_now()

    await repository.invalidate_active_password_reset_challenges(
        user_id=user.id,
        invalidated_at=now,
    )

    otp = generate_otp()

    otp_digest = hash_otp(
        otp
    )

    expires_at = (
        now
        + timedelta(
            minutes=settings.password_reset_otp_minutes
        )
    )

    challenge = (
        await repository.create_password_reset_challenge(
            user_id=user.id,
            otp_hash=otp_digest,
            expires_at=expires_at,
            max_attempts=settings.otp_max_attempts,
            requested_ip_address=requested_ip_address,
            requested_user_agent=requested_user_agent,
        )
    )

    return PasswordResetIssueResult(
        challenge=challenge,
        otp=otp,
        expires_at=expires_at,
    )


# =========================================================
# GET LATEST ACTIVE CHALLENGE
# =========================================================


async def get_latest_active_challenge(
    *,
    repository: AuthRepository,
    user: User,
) -> PasswordResetChallenge:
    """
    Return latest usable password-reset challenge.
    """

    challenge = (
        await repository.get_latest_password_reset_challenge(
            user.id
        )
    )

    if challenge is None:
        raise ResourceNotFound(
            "Password reset challenge was not found."
        )

    if is_challenge_consumed(
        challenge
    ):
        raise ValidationError(
            "Password reset challenge has already been used."
        )

    if is_challenge_invalidated(
        challenge
    ):
        raise ValidationError(
            "Password reset challenge is no longer valid."
        )

    if is_challenge_expired(
        challenge
    ):
        raise ValidationError(
            "Password reset OTP has expired."
        )

    if attempts_exhausted(
        challenge
    ):
        raise ValidationError(
            "Password reset OTP attempt limit has been reached."
        )

    return challenge


# =========================================================
# VERIFY PASSWORD RESET OTP
# =========================================================


async def verify_password_reset_otp(
    *,
    repository: AuthRepository,
    user: User,
    otp: str,
) -> PasswordResetVerificationResult:
    """
    Verify password-reset OTP and issue a temporary reset token.

    Flow:

        submitted OTP
            ↓
        find latest active challenge
            ↓
        verify OTP hash
            ↓
        invalid?
            increment attempts
            possibly invalidate
            reject
            ↓
        valid?
            generate random reset token
            ↓
        hash reset token
            ↓
        store hash + expiry
            ↓
        return raw reset token to user

    The reset token is NOT a login JWT.
    """

    challenge = (
        await get_latest_active_challenge(
            repository=repository,
            user=user,
        )
    )

    valid = verify_otp_hash(
        otp,
        challenge.otp_hash,
    )

    if not valid:
        attempt_count = (
            await repository.increment_password_reset_attempt(
                challenge
            )
        )

        remaining_attempts = max(
            0,
            challenge.max_attempts
            - attempt_count,
        )

        if remaining_attempts == 0:
            await repository.invalidate_password_reset_challenge(
                challenge,
                invalidated_at=utc_now(),
            )

            raise ValidationError(
                "Invalid OTP. Password reset attempt limit has been reached."
            )

        raise ValidationError(
            f"Invalid OTP. {remaining_attempts} attempt(s) remaining."
        )

    now = utc_now()

    reset_token = generate_secure_token(
        48
    )

    reset_token_digest = hash_token(
        reset_token
    )

    reset_token_expires_at = (
        now
        + timedelta(
            minutes=settings.password_reset_otp_minutes
        )
    )

    await repository.mark_password_reset_verified(
        challenge,
        verified_at=now,
        reset_token_hash=reset_token_digest,
        reset_token_expires_at=reset_token_expires_at,
    )

    return PasswordResetVerificationResult(
        challenge=challenge,
        reset_token=reset_token,
        reset_token_expires_at=reset_token_expires_at,
    )


# =========================================================
# RESET TOKEN VALIDATION
# =========================================================


async def validate_password_reset_token(
    *,
    repository: AuthRepository,
    reset_token: str,
) -> PasswordResetAuthorization:
    """
    Validate temporary password-reset authorization.

    Checks:

    - token is present
    - database challenge exists
    - challenge was OTP-verified
    - challenge not consumed
    - challenge not invalidated
    - reset token not expired
    - supplied token matches persisted HMAC

    Returns:
        PasswordResetAuthorization
    """

    if not reset_token:
        raise ValidationError(
            "Password reset token is required."
        )

    token_digest = hash_token(
        reset_token
    )

    challenge = (
        await repository.get_password_reset_by_reset_token_hash(
            token_digest
        )
    )

    if challenge is None:
        raise ValidationError(
            "Password reset token is invalid."
        )

    if challenge.verified_at is None:
        raise ValidationError(
            "Password reset challenge has not been verified."
        )

    if challenge.consumed_at is not None:
        raise ValidationError(
            "Password reset token has already been used."
        )

    if challenge.invalidated_at is not None:
        raise ValidationError(
            "Password reset token is no longer valid."
        )

    if (
        challenge.reset_token_hash
        is None
    ):
        raise ValidationError(
            "Password reset token is invalid."
        )

    if (
        challenge.reset_token_expires_at
        is None
    ):
        raise ValidationError(
            "Password reset token expiration is missing."
        )

    expires_at = _as_utc(
        challenge.reset_token_expires_at
    )

    if expires_at <= utc_now():
        raise ValidationError(
            "Password reset token has expired."
        )

    if not verify_token_hash(
        reset_token,
        challenge.reset_token_hash,
    ):
        raise ValidationError(
            "Password reset token is invalid."
        )

    return PasswordResetAuthorization(
        challenge=challenge,
        user_id=challenge.user_id,
        expires_at=expires_at,
    )


# =========================================================
# COMPLETE RESET CHALLENGE
# =========================================================


async def consume_password_reset(
    *,
    repository: AuthRepository,
    challenge: PasswordResetChallenge,
) -> PasswordResetChallenge:
    """
    Permanently consume the reset authorization after the password
    has successfully been changed.

    IMPORTANT:
    auth/service.py should only call this inside the same database
    transaction that updates the password and revokes sessions.
    """

    if challenge.consumed_at is not None:
        raise ValidationError(
            "Password reset challenge has already been used."
        )

    if challenge.invalidated_at is not None:
        raise ValidationError(
            "Password reset challenge is no longer valid."
        )

    return (
        await repository.consume_password_reset_challenge(
            challenge,
            consumed_at=utc_now(),
        )
    )


# =========================================================
# INVALIDATE USER RESET CHALLENGES
# =========================================================


async def invalidate_user_password_reset_challenges(
    *,
    repository: AuthRepository,
    user: User,
) -> int:
    """
    Invalidate every active password-reset challenge belonging
    to a user.

    Useful after:
    - successful password reset
    - security administration
    - account compromise response
    """

    return (
        await repository.invalidate_active_password_reset_challenges(
            user_id=user.id,
            invalidated_at=utc_now(),
        )
    )


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "PasswordResetIssueResult",
    "PasswordResetVerificationResult",
    "PasswordResetAuthorization",
    "utc_now",
    "get_password_reset_otp_expiry",
    "get_reset_token_expiry",
    "is_challenge_expired",
    "is_challenge_consumed",
    "is_challenge_invalidated",
    "attempts_exhausted",
    "is_challenge_verified",
    "challenge_is_active",
    "issue_password_reset",
    "get_latest_active_challenge",
    "verify_password_reset_otp",
    "validate_password_reset_token",
    "consume_password_reset",
    "invalidate_user_password_reset_challenges",
]