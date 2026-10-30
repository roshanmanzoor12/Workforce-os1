from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from app.config import settings
from app.core.exceptions import (
    ConflictError,
    ResourceNotFound,
    ValidationError,
)
from app.core.security import (
    generate_otp,
    hash_otp,
    verify_otp_hash,
)
from app.modules.auth.models import (
    EmailVerificationChallenge,
    User,
)
from app.modules.auth.repository import AuthRepository


# =========================================================
# RESULT TYPES
# =========================================================


@dataclass(slots=True)
class EmailVerificationIssueResult:
    """
    Result returned when a new verification OTP is created.

    IMPORTANT:
    otp is returned only to the service layer so it can be emailed.

    The plaintext OTP must never be stored in PostgreSQL.
    """

    challenge: EmailVerificationChallenge
    otp: str
    expires_at: datetime


@dataclass(slots=True)
class EmailVerificationResult:
    """
    Result returned after successful OTP verification.
    """

    user: User
    challenge: EmailVerificationChallenge
    verified_at: datetime


# =========================================================
# TIME HELPERS
# =========================================================


def utc_now() -> datetime:
    """
    Return timezone-aware UTC time.
    """

    return datetime.now(timezone.utc)


def get_verification_expiry() -> datetime:
    """
    Calculate verification OTP expiration using application settings.
    """

    return utc_now() + timedelta(
        minutes=settings.email_verification_otp_minutes
    )


# =========================================================
# REPOSITORY TRANSACTION HELPERS
# =========================================================


def _get_repository_session(
    repository: AuthRepository,
) -> Any:
    """
    Resolve the SQLAlchemy AsyncSession owned by AuthRepository.

    AuthRepository is the database access boundary for this module.

    Most implementations expose the session using one of:
        repository.session
        repository.db
        repository._session

    This compatibility helper allows the verification security counter
    to be committed before ValidationError leaves the request.

    Why this is necessary:

        wrong OTP
            ↓
        attempt_count += 1
            ↓
        flush
            ↓
        ValidationError
            ↓
        request handler rollback

    Without an explicit commit before the ValidationError, the failed
    attempt disappears from PostgreSQL and the attacker effectively
    receives unlimited OTP guesses.
    """

    for attribute_name in (
        "session",
        "db",
        "_session",
    ):
        session = getattr(
            repository,
            attribute_name,
            None,
        )

        if session is not None:
            return session

    raise RuntimeError(
        "AuthRepository does not expose its database session. "
        "Expected repository.session, repository.db, or "
        "repository._session."
    )


async def _commit_security_state(
    repository: AuthRepository,
) -> None:
    """
    Persist security-sensitive state before intentionally raising an
    authentication validation error.

    Normal successful auth flows can continue to use the transaction
    boundary owned by the service/router layer.

    Failed-attempt counters are different: they must survive the error
    response itself, otherwise the surrounding rollback destroys the
    brute-force protection state.
    """

    session = _get_repository_session(
        repository
    )

    await session.commit()


# =========================================================
# CHALLENGE STATE HELPERS
# =========================================================


def is_challenge_expired(
    challenge: EmailVerificationChallenge,
    *,
    now: datetime | None = None,
) -> bool:
    """
    Return True when an email verification challenge is expired.
    """

    current_time = now or utc_now()

    expires_at = challenge.expires_at

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(
            tzinfo=timezone.utc
        )

    return expires_at <= current_time


def is_challenge_consumed(
    challenge: EmailVerificationChallenge,
) -> bool:
    """
    Return True when challenge has already been consumed.
    """

    return challenge.consumed_at is not None


def is_challenge_invalidated(
    challenge: EmailVerificationChallenge,
) -> bool:
    """
    Return True when challenge was invalidated by resend/replacement.
    """

    return challenge.invalidated_at is not None


def attempts_exhausted(
    challenge: EmailVerificationChallenge,
) -> bool:
    """
    Return True when OTP attempt limit has been reached.
    """

    return (
        challenge.attempt_count
        >= challenge.max_attempts
    )


def challenge_is_active(
    challenge: EmailVerificationChallenge,
    *,
    now: datetime | None = None,
) -> bool:
    """
    Return True only when challenge is currently usable.
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
# ISSUE EMAIL VERIFICATION OTP
# =========================================================


async def issue_email_verification(
    *,
    repository: AuthRepository,
    user: User,
) -> EmailVerificationIssueResult:
    """
    Create a new email-verification OTP challenge.

    Flow:

        user
          ↓
        invalidate previous active challenges
          ↓
        generate secure numeric OTP
          ↓
        hash OTP using HMAC
          ↓
        store only OTP hash
          ↓
        return plaintext OTP to service layer
          ↓
        service sends OTP by email

    Raises:
        ConflictError
            when user email is already verified.
    """

    if user.is_email_verified:
        raise ConflictError(
            "Email address is already verified."
        )

    now = utc_now()

    # Prevent multiple simultaneous valid OTPs.
    await repository.invalidate_active_email_verification_challenges(
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
            minutes=settings.email_verification_otp_minutes
        )
    )

    challenge = (
        await repository.create_email_verification_challenge(
            user_id=user.id,
            otp_hash=otp_digest,
            expires_at=expires_at,
            max_attempts=settings.otp_max_attempts,
            sent_to_email=user.email,
        )
    )

    return EmailVerificationIssueResult(
        challenge=challenge,
        otp=otp,
        expires_at=expires_at,
    )


# =========================================================
# GET ACTIVE CHALLENGE
# =========================================================


async def get_latest_active_challenge(
    *,
    repository: AuthRepository,
    user: User,
) -> EmailVerificationChallenge:
    """
    Retrieve the most recent usable email verification challenge.

    Raises:
        ResourceNotFound
        ValidationError
    """

    challenge = (
        await repository.get_latest_email_verification_challenge(
            user.id
        )
    )

    if challenge is None:
        raise ResourceNotFound(
            "Email verification challenge was not found."
        )

    if challenge.consumed_at is not None:
        raise ValidationError(
            "Email verification challenge has already been used."
        )

    if challenge.invalidated_at is not None:
        raise ValidationError(
            "Email verification challenge is no longer valid."
        )

    if is_challenge_expired(
        challenge
    ):
        raise ValidationError(
            "Email verification OTP has expired."
        )

    if attempts_exhausted(
        challenge
    ):
        raise ValidationError(
            "Email verification OTP attempt limit has been reached."
        )

    return challenge


# =========================================================
# VERIFY OTP
# =========================================================


async def verify_email_otp(
    *,
    repository: AuthRepository,
    user: User,
    otp: str,
) -> EmailVerificationResult:
    """
    Verify a user's email OTP.

    Correct flow:

        find latest challenge
            ↓
        validate challenge state
            ↓
        compare submitted OTP against stored HMAC
            ↓
        if invalid:
            increment attempts
            ↓
            optionally invalidate when max reached
            ↓
            COMMIT SECURITY STATE
            ↓
            reject request
            ↓
        if valid:
            mark challenge verified/consumed
            ↓
            mark user email verified

    SECURITY REQUIREMENT:

    Failed OTP attempts must be committed before ValidationError is
    raised. Otherwise the outer request rollback removes attempt_count
    changes and the OTP attempt limit can effectively be bypassed.

    Raises:
        ConflictError
        ResourceNotFound
        ValidationError
    """

    if user.is_email_verified:
        raise ConflictError(
            "Email address is already verified."
        )

    challenge = await get_latest_active_challenge(
        repository=repository,
        user=user,
    )

    valid = verify_otp_hash(
        otp,
        challenge.otp_hash,
    )

    # -----------------------------------------------------
    # WRONG OTP
    # -----------------------------------------------------

    if not valid:
        attempt_count = (
            await repository.increment_email_verification_attempt(
                challenge
            )
        )

        remaining_attempts = max(
            0,
            challenge.max_attempts
            - attempt_count,
        )

        # -------------------------------------------------
        # ATTEMPT LIMIT REACHED
        # -------------------------------------------------

        if remaining_attempts == 0:
            await repository.invalidate_email_verification_challenge(
                challenge,
                invalidated_at=utc_now(),
            )

            # SECURITY CRITICAL:
            #
            # Save BOTH:
            #   attempt_count
            #   invalidated_at
            #
            # before ValidationError causes the outer request
            # transaction to roll back.
            await _commit_security_state(
                repository
            )

            raise ValidationError(
                "Invalid OTP. Verification attempt limit has been reached."
            )

        # -------------------------------------------------
        # ATTEMPTS REMAINING
        # -------------------------------------------------

        # SECURITY CRITICAL:
        #
        # Repository operations commonly flush but intentionally
        # do not commit. Since we intentionally raise immediately
        # afterward, the request's rollback would otherwise remove
        # the increment.
        await _commit_security_state(
            repository
        )

        raise ValidationError(
            f"Invalid OTP. {remaining_attempts} attempt(s) remaining."
        )

    # -----------------------------------------------------
    # CORRECT OTP
    # -----------------------------------------------------

    verified_at = utc_now()

    await repository.mark_email_verification_verified(
        challenge,
        verified_at=verified_at,
    )

    await repository.mark_email_verified(
        user,
        verified_at=verified_at,
    )

    return EmailVerificationResult(
        user=user,
        challenge=challenge,
        verified_at=verified_at,
    )


# =========================================================
# RESEND OTP
# =========================================================


async def resend_email_verification(
    *,
    repository: AuthRepository,
    user: User,
) -> EmailVerificationIssueResult:
    """
    Replace previous OTP with a newly generated challenge.

    Rate limiting is intentionally not implemented in this file.

    It will be enforced in the authentication service/router layer
    using Redis.

    This function ensures only one active challenge remains valid.
    """

    if user.is_email_verified:
        raise ConflictError(
            "Email address is already verified."
        )

    return await issue_email_verification(
        repository=repository,
        user=user,
    )


# =========================================================
# INVALIDATE ALL USER CHALLENGES
# =========================================================


async def invalidate_user_email_challenges(
    *,
    repository: AuthRepository,
    user: User,
) -> int:
    """
    Invalidate all active email verification challenges for a user.

    Useful for:
    - account administration
    - email change flow later
    - security cleanup
    """

    return (
        await repository.invalidate_active_email_verification_challenges(
            user_id=user.id,
            invalidated_at=utc_now(),
        )
    )


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "EmailVerificationIssueResult",
    "EmailVerificationResult",
    "utc_now",
    "get_verification_expiry",
    "is_challenge_expired",
    "is_challenge_consumed",
    "is_challenge_invalidated",
    "attempts_exhausted",
    "challenge_is_active",
    "issue_email_verification",
    "get_latest_active_challenge",
    "verify_email_otp",
    "resend_email_verification",
    "invalidate_user_email_challenges",
]