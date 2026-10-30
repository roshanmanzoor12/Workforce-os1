from __future__ import annotations

import hashlib
import hmac
import secrets


INVITATION_TOKEN_BYTES = 32


def normalize_invitation_email(
    email: str,
) -> str:
    normalized = (
        email
        .strip()
        .lower()
    )

    if not normalized:
        raise ValueError(
            "Invitation email "
            "cannot be empty."
        )

    if "@" not in normalized:
        raise ValueError(
            "Invalid invitation email."
        )

    return normalized


def generate_invitation_token(
) -> str:
    return secrets.token_urlsafe(
        INVITATION_TOKEN_BYTES
    )


def hash_invitation_token(
    token: str,
) -> str:
    if not token:
        raise ValueError(
            "Invitation token "
            "cannot be empty."
        )

    return hashlib.sha256(
        token.encode(
            "utf-8"
        )
    ).hexdigest()


def invitation_token_matches(
    *,
    token: str,
    token_hash: str,
) -> bool:
    candidate_hash = (
        hash_invitation_token(
            token
        )
    )

    return hmac.compare_digest(
        candidate_hash,
        token_hash,
    )


__all__ = [
    "INVITATION_TOKEN_BYTES",
    "normalize_invitation_email",
    "generate_invitation_token",
    "hash_invitation_token",
    "invitation_token_matches",
]