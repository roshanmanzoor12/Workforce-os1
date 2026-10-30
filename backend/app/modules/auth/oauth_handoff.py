from __future__ import annotations

import hashlib
import json
import secrets

from app.core.exceptions import InvalidToken
from app.core.redis import (
    build_redis_key,
    redis_client,
)
from app.modules.auth.schemas import (
    OAuthCallbackResponse,
)

OAUTH_HANDOFF_TTL_SECONDS = 90

OAUTH_HANDOFF_NAMESPACE = (
    "auth",
    "oauth-handoff",
)


def _code_digest(
    code: str,
) -> str:
    return hashlib.sha256(
        code.encode("utf-8")
    ).hexdigest()


def _redis_key(
    code: str,
) -> str:
    return build_redis_key(
        *OAUTH_HANDOFF_NAMESPACE,
        _code_digest(code),
    )


async def create_oauth_handoff(
    result: OAuthCallbackResponse,
) -> str:
    """
    Store a completed WorkforceOS OAuth authentication
    result behind a short-lived, one-time code.

    Access and refresh tokens are never placed in the
    browser redirect URL.
    """

    payload = json.dumps(
        result.model_dump(
            mode="json",
        ),
        separators=(
            ",",
            ":",
        ),
    )

    for _attempt in range(5):
        code = secrets.token_urlsafe(
            32
        )

        created = (
            await redis_client.set(
                _redis_key(code),
                payload,
                ex=OAUTH_HANDOFF_TTL_SECONDS,
                nx=True,
            )
        )

        if created:
            return code

    raise RuntimeError(
        "Unable to create OAuth handoff code."
    )


async def consume_oauth_handoff(
    code: str,
) -> OAuthCallbackResponse:
    """
    Atomically consume a one-time OAuth handoff code.

    Redis GETDEL guarantees that one valid handoff code
    cannot be exchanged more than once.
    """

    normalized_code = (
        code.strip()
    )

    if not normalized_code:
        raise InvalidToken(
            "OAuth exchange code is invalid."
        )

    raw = await redis_client.getdel(
        _redis_key(
            normalized_code
        )
    )

    if raw is None:
        raise InvalidToken(
            "OAuth exchange code is invalid or expired."
        )

    if isinstance(
        raw,
        bytes,
    ):
        raw = raw.decode(
            "utf-8"
        )

    try:
        return (
            OAuthCallbackResponse.model_validate_json(
                raw
            )
        )
    except Exception as exc:
        raise InvalidToken(
            "OAuth exchange data is invalid."
        ) from exc


__all__ = [
    "OAUTH_HANDOFF_TTL_SECONDS",
    "create_oauth_handoff",
    "consume_oauth_handoff",
]