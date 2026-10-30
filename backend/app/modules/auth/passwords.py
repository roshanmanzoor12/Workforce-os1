from __future__ import annotations

import re
from dataclasses import dataclass

from app.config import settings
from app.core.security import (
    hash_password as core_hash_password,
    verify_password as core_verify_password,
)


# =========================================================
# PASSWORD POLICY RESULT
# =========================================================


@dataclass(slots=True)
class PasswordPolicyResult:
    """
    Result returned by password-policy validation.

    valid:
        True when the password satisfies all configured rules.

    errors:
        Human-readable validation failures.
    """

    valid: bool
    errors: list[str]


# =========================================================
# PASSWORD POLICY
# =========================================================


def validate_password_policy(
    password: str,
) -> PasswordPolicyResult:
    """
    Validate a plaintext password against WorkforceOS policy.

    This function does NOT hash the password.

    Current policy comes from settings:

        PASSWORD_MIN_LENGTH
        PASSWORD_REQUIRE_LETTER
        PASSWORD_REQUIRE_NUMBER
        PASSWORD_REQUIRE_SPECIAL

    Returns:
        PasswordPolicyResult
    """

    errors: list[str] = []

    if not isinstance(password, str):
        return PasswordPolicyResult(
            valid=False,
            errors=[
                "Password must be a string."
            ],
        )

    if len(password) < settings.password_min_length:
        errors.append(
            f"Password must contain at least "
            f"{settings.password_min_length} characters."
        )

    if len(password) > 128:
        errors.append(
            "Password must contain at most 128 characters."
        )

    if settings.password_require_letter:
        if not re.search(
            r"[A-Za-z]",
            password,
        ):
            errors.append(
                "Password must contain at least one letter."
            )

    if settings.password_require_number:
        if not re.search(
            r"\d",
            password,
        ):
            errors.append(
                "Password must contain at least one number."
            )

    if settings.password_require_special:
        if not re.search(
            r"[^A-Za-z0-9]",
            password,
        ):
            errors.append(
                "Password must contain at least one special character."
            )

    return PasswordPolicyResult(
        valid=len(errors) == 0,
        errors=errors,
    )


# =========================================================
# PASSWORD POLICY ENFORCEMENT
# =========================================================


def ensure_password_policy(
    password: str,
) -> None:
    """
    Validate a password and raise ValueError when policy fails.

    This helper is useful in service-layer flows where a password
    must be rejected immediately.

    Example:

        ensure_password_policy(request.password)

    Raises:
        ValueError
    """

    result = validate_password_policy(
        password
    )

    if result.valid:
        return

    raise ValueError(
        " ".join(
            result.errors
        )
    )


# =========================================================
# PASSWORD HASHING
# =========================================================


def hash_password(
    password: str,
) -> str:
    """
    Validate and securely hash a plaintext password.

    Workflow:

        plaintext password
            ↓
        policy validation
            ↓
        Argon2 hashing
            ↓
        encoded hash

    Plaintext passwords must never be written to:
    - PostgreSQL
    - Redis
    - logs
    - audit events
    """

    ensure_password_policy(
        password
    )

    return core_hash_password(
        password
    )


# =========================================================
# PASSWORD VERIFICATION
# =========================================================


def verify_password(
    password: str,
    hashed_password: str | None,
) -> bool:
    """
    Verify a plaintext password against a stored hash.

    Returns False when:
    - password is empty
    - stored hash is missing
    - stored hash is malformed
    - password does not match
    """

    if not password:
        return False

    if not hashed_password:
        return False

    return core_verify_password(
        password,
        hashed_password,
    )


# =========================================================
# PASSWORD MATCHING
# =========================================================


def ensure_passwords_match(
    password: str,
    confirm_password: str,
) -> None:
    """
    Ensure two password fields match.

    Used in:
    - signup
    - password reset
    - change password

    Raises:
        ValueError
    """

    if password != confirm_password:
        raise ValueError(
            "Password and confirm password do not match."
        )


# =========================================================
# NEW PASSWORD VALIDATION
# =========================================================


def validate_new_password(
    *,
    new_password: str,
    confirm_password: str,
    current_password: str | None = None,
) -> None:
    """
    Validate a password during password creation/change/reset.

    Rules:
    - new password must satisfy configured password policy
    - confirmation must match
    - optionally reject reuse of the currently supplied plaintext
      password when current_password is provided

    NOTE:
    Proper historical password-reuse prevention will later require
    stored password-history hashes. This function only handles the
    immediate current-password comparison.
    """

    ensure_passwords_match(
        new_password,
        confirm_password,
    )

    ensure_password_policy(
        new_password
    )

    if (
        current_password is not None
        and new_password == current_password
    ):
        raise ValueError(
            "New password must be different from the current password."
        )


# =========================================================
# PASSWORD STRENGTH METADATA
# =========================================================


def password_policy_metadata() -> dict[str, object]:
    """
    Return non-sensitive password-policy information.

    Useful for:
    - signup UI
    - reset-password UI
    - admin security settings display

    This does not expose secrets.
    """

    return {
        "minimum_length": settings.password_min_length,
        "maximum_length": 128,
        "require_letter": settings.password_require_letter,
        "require_number": settings.password_require_number,
        "require_special": settings.password_require_special,
    }


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "PasswordPolicyResult",
    "validate_password_policy",
    "ensure_password_policy",
    "hash_password",
    "verify_password",
    "ensure_passwords_match",
    "validate_new_password",
    "password_policy_metadata",
]