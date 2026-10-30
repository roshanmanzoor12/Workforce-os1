from __future__ import annotations

import os
from dataclasses import dataclass


TRUE_VALUES = {
    "1",
    "true",
    "yes",
    "on",
}


def _env_bool(
    name: str,
    default: bool = False,
) -> bool:
    value = os.getenv(
        name
    )

    if value is None:
        return default

    return (
        value.strip().lower()
        in TRUE_VALUES
    )


def _env_int(
    name: str,
    default: int,
    minimum: int,
    maximum: int,
) -> int:
    raw = os.getenv(
        name
    )

    if raw is None:
        return default

    try:
        value = int(
            raw
        )
    except ValueError as exc:
        raise ValueError(
            f"{name} must be an integer."
        ) from exc

    if (
        value < minimum
        or value > maximum
    ):
        raise ValueError(
            f"{name} must be between "
            f"{minimum} and {maximum}."
        )

    return value


@dataclass(
    frozen=True,
    slots=True,
)
class AIProductivitySettings:
    enabled: bool

    provider_key: str

    endpoint: str | None

    model_key: str | None

    bearer_token: str | None

    request_timeout_seconds: int

    max_item_characters: int

    max_context_characters: int

    allow_external_processing: bool


def get_ai_productivity_settings(
) -> AIProductivitySettings:
    enabled = _env_bool(
        "WORKFORCE_AI_PRODUCTIVITY_ENABLED",
        False,
    )

    allow_external = _env_bool(
        (
            "WORKFORCE_AI_PRODUCTIVITY_"
            "ALLOW_EXTERNAL_PROCESSING"
        ),
        False,
    )

    provider_key = os.getenv(
        "WORKFORCE_AI_PRODUCTIVITY_PROVIDER",
        "disabled",
    ).strip().lower()

    endpoint = os.getenv(
        "WORKFORCE_AI_PRODUCTIVITY_ENDPOINT"
    )

    if endpoint is not None:
        endpoint = (
            endpoint.strip()
            or None
        )

    model_key = os.getenv(
        "WORKFORCE_AI_PRODUCTIVITY_MODEL"
    )

    if model_key is not None:
        model_key = (
            model_key.strip()
            or None
        )

    bearer_token = os.getenv(
        (
            "WORKFORCE_AI_PRODUCTIVITY_"
            "BEARER_TOKEN"
        )
    )

    if bearer_token is not None:
        bearer_token = (
            bearer_token.strip()
            or None
        )

    return AIProductivitySettings(
        enabled=enabled,
        provider_key=provider_key,
        endpoint=endpoint,
        model_key=model_key,
        bearer_token=bearer_token,
        request_timeout_seconds=(
            _env_int(
                (
                    "WORKFORCE_AI_PRODUCTIVITY_"
                    "TIMEOUT_SECONDS"
                ),
                default=30,
                minimum=1,
                maximum=120,
            )
        ),
        max_item_characters=(
            _env_int(
                (
                    "WORKFORCE_AI_PRODUCTIVITY_"
                    "MAX_ITEM_CHARACTERS"
                ),
                default=4000,
                minimum=500,
                maximum=20000,
            )
        ),
        max_context_characters=(
            _env_int(
                (
                    "WORKFORCE_AI_PRODUCTIVITY_"
                    "MAX_CONTEXT_CHARACTERS"
                ),
                default=30000,
                minimum=2000,
                maximum=100000,
            )
        ),
        allow_external_processing=(
            allow_external
        ),
    )


__all__ = [
    "AIProductivitySettings",
    "get_ai_productivity_settings",
]