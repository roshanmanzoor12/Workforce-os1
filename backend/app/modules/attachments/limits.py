from __future__ import annotations

import os


MIB = 1024 * 1024


DEFAULT_LIMITS = {
    "FREE": 10 * MIB,
    "STARTER": 50 * MIB,
    "PROFESSIONAL": 250 * MIB,
    "BUSINESS": 1024 * MIB,
}


def _read_positive_int(
    environment_name: str,
    default: int,
) -> int:
    raw = os.getenv(environment_name)

    if raw is None or not raw.strip():
        return default

    try:
        value = int(raw)
    except ValueError:
        return default

    if value <= 0:
        return default

    return value


def get_attachment_limit_bytes(
    plan_code: str | None,
) -> int:
    normalized = (plan_code or "FREE").strip().upper()

    if normalized not in DEFAULT_LIMITS:
        normalized = "FREE"

    default = DEFAULT_LIMITS[normalized]

    env_name = (
        "WORKFORCE_ATTACHMENT_"
        + normalized
        + "_MAX_BYTES"
    )

    return _read_positive_int(
        env_name,
        default,
    )


def get_attachment_limit_mb(
    plan_code: str | None,
) -> int:
    value = get_attachment_limit_bytes(plan_code)

    return value // MIB


def validate_attachment_size(
    *,
    plan_code: str | None,
    size_bytes: int,
) -> int:
    if size_bytes <= 0:
        raise ValueError(
            "Attachment size must be greater than zero."
        )

    limit = get_attachment_limit_bytes(plan_code)

    if size_bytes > limit:
        plan = (plan_code or "FREE").upper()

        raise ValueError(
            f"Attachment exceeds {plan} plan limit "
            f"of {limit // MIB} MB."
        )

    return limit