from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal


# =========================================================
# EVENT TYPES
# =========================================================


AuthEventName = Literal[
    "user_registered",
    "email_verification_requested",
    "email_verified",
    "email_verification_failed",
    "login_succeeded",
    "login_failed",
    "logout_succeeded",
    "logout_all_succeeded",
    "refresh_succeeded",
    "refresh_failed",
    "password_reset_requested",
    "password_reset_otp_verified",
    "password_reset_failed",
    "password_changed",
    "session_created",
    "session_rotated",
    "session_revoked",
    "all_sessions_revoked",
    "oauth_login_succeeded",
    "oauth_login_failed",
    "oauth_identity_linked",
    "oauth_identity_unlinked",
    "account_locked",
    "account_unlocked",
    "account_disabled",
    "account_enabled",
]


AuthProvider = Literal[
    "local",
    "google",
    "github",
]


AuthEventSeverity = Literal[
    "info",
    "warning",
    "critical",
]


# =========================================================
# BASE EVENT
# =========================================================


@dataclass(slots=True)
class AuthEvent:
    """
    Standard WorkforceOS authentication domain event.

    These events represent meaningful authentication/security actions.

    They are NOT database audit records by themselves.

    Later flow:

        auth/service.py
            ↓
        AuthEvent
            ↓
        event dispatcher
            ↓
        audit module
        security monitoring
        notifications
        analytics
        platform-admin activity
    """

    name: AuthEventName

    occurred_at: datetime = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )

    event_id: str = field(
        default_factory=lambda: str(
            uuid.uuid4()
        )
    )

    user_id: uuid.UUID | None = None

    session_id: uuid.UUID | None = None

    provider: AuthProvider | None = None

    severity: AuthEventSeverity = "info"

    ip_address: str | None = None

    user_agent: str | None = None

    request_id: str | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        """
        Convert event into a JSON-friendly dictionary.
        """

        payload = asdict(
            self
        )

        payload["occurred_at"] = (
            self.occurred_at.isoformat()
        )

        if self.user_id is not None:
            payload["user_id"] = str(
                self.user_id
            )

        if self.session_id is not None:
            payload["session_id"] = str(
                self.session_id
            )

        return payload


# =========================================================
# SAFE METADATA FILTERING
# =========================================================


SENSITIVE_METADATA_FIELDS = {
    "password",
    "password_hash",
    "new_password",
    "confirm_password",
    "otp",
    "otp_hash",
    "token",
    "access_token",
    "refresh_token",
    "reset_token",
    "reset_token_hash",
    "authorization",
    "client_secret",
    "secret",
}


def sanitize_event_metadata(
    metadata: dict[str, Any] | None,
) -> dict[str, Any]:
    """
    Remove sensitive values from authentication event metadata.

    Authentication domain events must NEVER contain:
    - plaintext passwords
    - OTPs
    - access tokens
    - refresh tokens
    - password-reset tokens
    - client secrets
    """

    if not metadata:
        return {}

    sanitized: dict[str, Any] = {}

    for key, value in metadata.items():
        if key.lower() in SENSITIVE_METADATA_FIELDS:
            sanitized[key] = "[REDACTED]"
        else:
            sanitized[key] = value

    return sanitized


# =========================================================
# GENERIC EVENT FACTORY
# =========================================================


def create_auth_event(
    name: AuthEventName,
    *,
    user_id: uuid.UUID | None = None,
    session_id: uuid.UUID | None = None,
    provider: AuthProvider | None = None,
    severity: AuthEventSeverity = "info",
    ip_address: str | None = None,
    user_agent: str | None = None,
    request_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuthEvent:
    """
    Create a standardized authentication domain event.
    """

    return AuthEvent(
        name=name,
        user_id=user_id,
        session_id=session_id,
        provider=provider,
        severity=severity,
        ip_address=ip_address,
        user_agent=user_agent,
        request_id=request_id,
        metadata=sanitize_event_metadata(
            metadata
        ),
    )


# =========================================================
# USER REGISTRATION EVENTS
# =========================================================


def user_registered_event(
    *,
    user_id: uuid.UUID,
    provider: AuthProvider = "local",
    ip_address: str | None = None,
    user_agent: str | None = None,
    request_id: str | None = None,
) -> AuthEvent:
    return create_auth_event(
        "user_registered",
        user_id=user_id,
        provider=provider,
        ip_address=ip_address,
        user_agent=user_agent,
        request_id=request_id,
    )


# =========================================================
# EMAIL VERIFICATION EVENTS
# =========================================================


def email_verification_requested_event(
    *,
    user_id: uuid.UUID,
    ip_address: str | None = None,
    request_id: str | None = None,
) -> AuthEvent:
    return create_auth_event(
        "email_verification_requested",
        user_id=user_id,
        ip_address=ip_address,
        request_id=request_id,
    )


def email_verified_event(
    *,
    user_id: uuid.UUID,
    request_id: str | None = None,
) -> AuthEvent:
    return create_auth_event(
        "email_verified",
        user_id=user_id,
        request_id=request_id,
    )


def email_verification_failed_event(
    *,
    user_id: uuid.UUID | None = None,
    ip_address: str | None = None,
    request_id: str | None = None,
    reason: str | None = None,
) -> AuthEvent:
    return create_auth_event(
        "email_verification_failed",
        user_id=user_id,
        severity="warning",
        ip_address=ip_address,
        request_id=request_id,
        metadata={
            "reason": reason,
        },
    )


# =========================================================
# LOGIN EVENTS
# =========================================================


def login_succeeded_event(
    *,
    user_id: uuid.UUID,
    session_id: uuid.UUID,
    provider: AuthProvider = "local",
    ip_address: str | None = None,
    user_agent: str | None = None,
    request_id: str | None = None,
) -> AuthEvent:
    return create_auth_event(
        "login_succeeded",
        user_id=user_id,
        session_id=session_id,
        provider=provider,
        ip_address=ip_address,
        user_agent=user_agent,
        request_id=request_id,
    )


def login_failed_event(
    *,
    user_id: uuid.UUID | None = None,
    provider: AuthProvider = "local",
    ip_address: str | None = None,
    user_agent: str | None = None,
    request_id: str | None = None,
    reason: str | None = None,
) -> AuthEvent:
    return create_auth_event(
        "login_failed",
        user_id=user_id,
        provider=provider,
        severity="warning",
        ip_address=ip_address,
        user_agent=user_agent,
        request_id=request_id,
        metadata={
            "reason": reason,
        },
    )


# =========================================================
# SESSION EVENTS
# =========================================================


def session_created_event(
    *,
    user_id: uuid.UUID,
    session_id: uuid.UUID,
    ip_address: str | None = None,
    user_agent: str | None = None,
    request_id: str | None = None,
) -> AuthEvent:
    return create_auth_event(
        "session_created",
        user_id=user_id,
        session_id=session_id,
        ip_address=ip_address,
        user_agent=user_agent,
        request_id=request_id,
    )


def session_rotated_event(
    *,
    user_id: uuid.UUID,
    session_id: uuid.UUID,
    replacement_session_id: uuid.UUID,
    request_id: str | None = None,
) -> AuthEvent:
    return create_auth_event(
        "session_rotated",
        user_id=user_id,
        session_id=session_id,
        request_id=request_id,
        metadata={
            "replacement_session_id": str(
                replacement_session_id
            ),
        },
    )


def session_revoked_event(
    *,
    user_id: uuid.UUID,
    session_id: uuid.UUID,
    reason: str | None = None,
    request_id: str | None = None,
) -> AuthEvent:
    return create_auth_event(
        "session_revoked",
        user_id=user_id,
        session_id=session_id,
        request_id=request_id,
        metadata={
            "reason": reason,
        },
    )


def all_sessions_revoked_event(
    *,
    user_id: uuid.UUID,
    revoked_sessions: int,
    reason: str | None = None,
    request_id: str | None = None,
) -> AuthEvent:
    return create_auth_event(
        "all_sessions_revoked",
        user_id=user_id,
        request_id=request_id,
        metadata={
            "revoked_sessions": revoked_sessions,
            "reason": reason,
        },
    )


# =========================================================
# REFRESH EVENTS
# =========================================================


def refresh_succeeded_event(
    *,
    user_id: uuid.UUID,
    session_id: uuid.UUID,
    request_id: str | None = None,
) -> AuthEvent:
    return create_auth_event(
        "refresh_succeeded",
        user_id=user_id,
        session_id=session_id,
        request_id=request_id,
    )


def refresh_failed_event(
    *,
    user_id: uuid.UUID | None = None,
    session_id: uuid.UUID | None = None,
    request_id: str | None = None,
    reason: str | None = None,
) -> AuthEvent:
    return create_auth_event(
        "refresh_failed",
        user_id=user_id,
        session_id=session_id,
        severity="warning",
        request_id=request_id,
        metadata={
            "reason": reason,
        },
    )


# =========================================================
# LOGOUT EVENTS
# =========================================================


def logout_succeeded_event(
    *,
    user_id: uuid.UUID,
    session_id: uuid.UUID,
    request_id: str | None = None,
) -> AuthEvent:
    return create_auth_event(
        "logout_succeeded",
        user_id=user_id,
        session_id=session_id,
        request_id=request_id,
    )


def logout_all_succeeded_event(
    *,
    user_id: uuid.UUID,
    revoked_sessions: int,
    request_id: str | None = None,
) -> AuthEvent:
    return create_auth_event(
        "logout_all_succeeded",
        user_id=user_id,
        request_id=request_id,
        metadata={
            "revoked_sessions": revoked_sessions,
        },
    )


# =========================================================
# PASSWORD RESET EVENTS
# =========================================================


def password_reset_requested_event(
    *,
    user_id: uuid.UUID | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    request_id: str | None = None,
) -> AuthEvent:
    return create_auth_event(
        "password_reset_requested",
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        request_id=request_id,
    )


def password_reset_otp_verified_event(
    *,
    user_id: uuid.UUID,
    request_id: str | None = None,
) -> AuthEvent:
    return create_auth_event(
        "password_reset_otp_verified",
        user_id=user_id,
        request_id=request_id,
    )


def password_reset_failed_event(
    *,
    user_id: uuid.UUID | None = None,
    ip_address: str | None = None,
    request_id: str | None = None,
    reason: str | None = None,
) -> AuthEvent:
    return create_auth_event(
        "password_reset_failed",
        user_id=user_id,
        severity="warning",
        ip_address=ip_address,
        request_id=request_id,
        metadata={
            "reason": reason,
        },
    )


def password_changed_event(
    *,
    user_id: uuid.UUID,
    request_id: str | None = None,
) -> AuthEvent:
    return create_auth_event(
        "password_changed",
        user_id=user_id,
        severity="warning",
        request_id=request_id,
    )


# =========================================================
# OAUTH EVENTS
# =========================================================


def oauth_login_succeeded_event(
    *,
    user_id: uuid.UUID,
    session_id: uuid.UUID,
    provider: Literal[
        "google",
        "github",
    ],
    ip_address: str | None = None,
    user_agent: str | None = None,
    request_id: str | None = None,
) -> AuthEvent:
    return create_auth_event(
        "oauth_login_succeeded",
        user_id=user_id,
        session_id=session_id,
        provider=provider,
        ip_address=ip_address,
        user_agent=user_agent,
        request_id=request_id,
    )


def oauth_login_failed_event(
    *,
    provider: Literal[
        "google",
        "github",
    ],
    user_id: uuid.UUID | None = None,
    reason: str | None = None,
    ip_address: str | None = None,
    request_id: str | None = None,
) -> AuthEvent:
    return create_auth_event(
        "oauth_login_failed",
        user_id=user_id,
        provider=provider,
        severity="warning",
        ip_address=ip_address,
        request_id=request_id,
        metadata={
            "reason": reason,
        },
    )


def oauth_identity_linked_event(
    *,
    user_id: uuid.UUID,
    provider: Literal[
        "google",
        "github",
    ],
    request_id: str | None = None,
) -> AuthEvent:
    return create_auth_event(
        "oauth_identity_linked",
        user_id=user_id,
        provider=provider,
        request_id=request_id,
    )


def oauth_identity_unlinked_event(
    *,
    user_id: uuid.UUID,
    provider: Literal[
        "google",
        "github",
    ],
    request_id: str | None = None,
) -> AuthEvent:
    return create_auth_event(
        "oauth_identity_unlinked",
        user_id=user_id,
        provider=provider,
        severity="warning",
        request_id=request_id,
    )


# =========================================================
# ACCOUNT SECURITY EVENTS
# =========================================================


def account_locked_event(
    *,
    user_id: uuid.UUID,
    reason: str | None = None,
    request_id: str | None = None,
) -> AuthEvent:
    return create_auth_event(
        "account_locked",
        user_id=user_id,
        severity="critical",
        request_id=request_id,
        metadata={
            "reason": reason,
        },
    )


def account_unlocked_event(
    *,
    user_id: uuid.UUID,
    request_id: str | None = None,
) -> AuthEvent:
    return create_auth_event(
        "account_unlocked",
        user_id=user_id,
        severity="warning",
        request_id=request_id,
    )


def account_disabled_event(
    *,
    user_id: uuid.UUID,
    reason: str | None = None,
    request_id: str | None = None,
) -> AuthEvent:
    return create_auth_event(
        "account_disabled",
        user_id=user_id,
        severity="critical",
        request_id=request_id,
        metadata={
            "reason": reason,
        },
    )


def account_enabled_event(
    *,
    user_id: uuid.UUID,
    request_id: str | None = None,
) -> AuthEvent:
    return create_auth_event(
        "account_enabled",
        user_id=user_id,
        severity="warning",
        request_id=request_id,
    )


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "AuthEventName",
    "AuthProvider",
    "AuthEventSeverity",
    "AuthEvent",
    "sanitize_event_metadata",
    "create_auth_event",
    "user_registered_event",
    "email_verification_requested_event",
    "email_verified_event",
    "email_verification_failed_event",
    "login_succeeded_event",
    "login_failed_event",
    "session_created_event",
    "session_rotated_event",
    "session_revoked_event",
    "all_sessions_revoked_event",
    "refresh_succeeded_event",
    "refresh_failed_event",
    "logout_succeeded_event",
    "logout_all_succeeded_event",
    "password_reset_requested_event",
    "password_reset_otp_verified_event",
    "password_reset_failed_event",
    "password_changed_event",
    "oauth_login_succeeded_event",
    "oauth_login_failed_event",
    "oauth_identity_linked_event",
    "oauth_identity_unlinked_event",
    "account_locked_event",
    "account_unlocked_event",
    "account_disabled_event",
    "account_enabled_event",
]