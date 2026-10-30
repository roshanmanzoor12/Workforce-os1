from __future__ import annotations

from pathlib import Path


ROOT = Path(
    "app/modules/ai_productivity"
)


def test_no_tenant_database_credentials() -> None:
    forbidden = [
        "database_name",
        "tenant_password",
        "database_password",
        "postgresql://",
        "asyncpg://",
    ]

    for path in ROOT.glob(
        "*.py"
    ):
        text = path.read_text(
            encoding="utf-8",
        ).lower()

        for token in forbidden:
            assert token not in text


def test_no_request_state_tenant_session() -> None:
    for path in ROOT.glob(
        "*.py"
    ):
        text = path.read_text(
            encoding="utf-8",
        )

        assert (
            "request.state"
            not in text
        )


def test_external_processing_has_explicit_gate() -> None:
    provider_text = (
        ROOT
        / "provider.py"
    ).read_text(
        encoding="utf-8",
    )

    config_text = (
        ROOT
        / "config.py"
    ).read_text(
        encoding="utf-8",
    )

    assert (
        "allow_external_processing"
        in provider_text
    )

    assert (
        "ALLOW_EXTERNAL_PROCESSING"
        in config_text
    )


def test_context_has_size_controls() -> None:
    privacy = (
        ROOT
        / "privacy.py"
    ).read_text(
        encoding="utf-8",
    )

    assert (
        "max_item_characters"
        in privacy
    )

    assert (
        "max_context_characters"
        in privacy
    )


def test_provider_token_not_exposed_in_schema() -> None:
    schema_text = Path(
        "app/modules/"
        "ai_productivity/"
        "schemas.py"
    ).read_text(
        encoding="utf-8",
    ).lower()

    assert (
        "bearer_token"
        not in schema_text
    )