from __future__ import annotations

from app.modules.ai_productivity.http_provider import (
    HTTPJSONAIProductivityProvider,
)
from app.modules.ai_productivity.provider import (
    DisabledAIProductivityProvider,
    get_ai_productivity_provider,
)


def clear_ai_environment(
    monkeypatch,
) -> None:
    names = [
        "WORKFORCE_AI_PRODUCTIVITY_ENABLED",
        (
            "WORKFORCE_AI_PRODUCTIVITY_"
            "ALLOW_EXTERNAL_PROCESSING"
        ),
        "WORKFORCE_AI_PRODUCTIVITY_PROVIDER",
        "WORKFORCE_AI_PRODUCTIVITY_ENDPOINT",
        "WORKFORCE_AI_PRODUCTIVITY_MODEL",
        (
            "WORKFORCE_AI_PRODUCTIVITY_"
            "BEARER_TOKEN"
        ),
    ]

    for name in names:
        monkeypatch.delenv(
            name,
            raising=False,
        )


def test_provider_disabled_by_default(
    monkeypatch,
) -> None:
    clear_ai_environment(
        monkeypatch
    )

    provider = (
        get_ai_productivity_provider()
    )

    assert isinstance(
        provider,
        DisabledAIProductivityProvider,
    )

    assert (
        provider.info()
        .external_processing_enabled
        is False
    )


def test_enabled_without_external_permission_is_disabled(
    monkeypatch,
) -> None:
    clear_ai_environment(
        monkeypatch
    )

    monkeypatch.setenv(
        "WORKFORCE_AI_PRODUCTIVITY_ENABLED",
        "true",
    )

    monkeypatch.setenv(
        "WORKFORCE_AI_PRODUCTIVITY_PROVIDER",
        "http_json",
    )

    monkeypatch.setenv(
        "WORKFORCE_AI_PRODUCTIVITY_ENDPOINT",
        "https://example.invalid/ai",
    )

    provider = (
        get_ai_productivity_provider()
    )

    assert isinstance(
        provider,
        DisabledAIProductivityProvider,
    )


def test_http_provider_requires_explicit_opt_in(
    monkeypatch,
) -> None:
    clear_ai_environment(
        monkeypatch
    )

    monkeypatch.setenv(
        "WORKFORCE_AI_PRODUCTIVITY_ENABLED",
        "true",
    )

    monkeypatch.setenv(
        (
            "WORKFORCE_AI_PRODUCTIVITY_"
            "ALLOW_EXTERNAL_PROCESSING"
        ),
        "true",
    )

    monkeypatch.setenv(
        "WORKFORCE_AI_PRODUCTIVITY_PROVIDER",
        "http_json",
    )

    monkeypatch.setenv(
        "WORKFORCE_AI_PRODUCTIVITY_ENDPOINT",
        "https://example.invalid/ai",
    )

    provider = (
        get_ai_productivity_provider()
    )

    assert isinstance(
        provider,
        HTTPJSONAIProductivityProvider,
    )

    assert (
        provider.info()
        .external_processing_enabled
        is True
    )


def test_unknown_provider_stays_disabled(
    monkeypatch,
) -> None:
    clear_ai_environment(
        monkeypatch
    )

    monkeypatch.setenv(
        "WORKFORCE_AI_PRODUCTIVITY_ENABLED",
        "true",
    )

    monkeypatch.setenv(
        (
            "WORKFORCE_AI_PRODUCTIVITY_"
            "ALLOW_EXTERNAL_PROCESSING"
        ),
        "true",
    )

    monkeypatch.setenv(
        "WORKFORCE_AI_PRODUCTIVITY_PROVIDER",
        "unknown_vendor",
    )

    provider = (
        get_ai_productivity_provider()
    )

    assert isinstance(
        provider,
        DisabledAIProductivityProvider,
    )