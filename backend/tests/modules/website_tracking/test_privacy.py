from __future__ import annotations

import pytest

from app.modules.website_tracking.privacy import (
    WebsiteTrackingPrivacyPolicy,
    normalize_domain,
)


@pytest.mark.parametrize(
    (
        "input_value",
        "expected",
    ),
    [
        (
            "github.com",
            "github.com",
        ),
        (
            "GITHUB.COM",
            "github.com",
        ),
        (
            "www.github.com",
            "github.com",
        ),
        (
            "https://github.com/openai/test",
            "github.com",
        ),
        (
            "https://www.example.com/a?token=secret",
            "example.com",
        ),
        (
            "example.com:443",
            "example.com",
        ),
        (
            "docs.example.com",
            "docs.example.com",
        ),
        (
            "127.0.0.1",
            "127.0.0.1",
        ),
    ],
)
def test_normalize_domain(
    input_value: str,
    expected: str,
) -> None:
    assert (
        normalize_domain(
            input_value
        )
        == expected
    )


@pytest.mark.parametrize(
    "invalid_value",
    [
        "",
        "   ",
        ".",
        "example..com",
        "-example.com",
        "example-.com",
    ],
)
def test_invalid_domains_are_rejected(
    invalid_value: str,
) -> None:
    with pytest.raises(
        ValueError
    ):
        normalize_domain(
            invalid_value
        )


def test_default_policy_suppresses_url(
) -> None:
    policy = (
        WebsiteTrackingPrivacyPolicy()
    )

    result = (
        policy.sanitize_page_url(
            (
                "https://example.com/private"
                "?password=secret#section"
            )
        )
    )

    assert result is None


def test_default_policy_suppresses_title(
) -> None:
    policy = (
        WebsiteTrackingPrivacyPolicy()
    )

    assert (
        policy.sanitize_page_title(
            "Private document"
        )
        is None
    )


def test_url_policy_removes_query_and_fragment(
) -> None:
    policy = (
        WebsiteTrackingPrivacyPolicy(
            capture_page_urls=True,
        )
    )

    result = (
        policy.sanitize_page_url(
            (
                "https://www.example.com/account"
                "?token=secret#password"
            )
        )
    )

    assert (
        result
        == "https://example.com/account"
    )

    assert "secret" not in result
    assert "token" not in result
    assert "#" not in result


def test_title_capture_requires_explicit_enable(
) -> None:
    policy = (
        WebsiteTrackingPrivacyPolicy(
            capture_page_titles=True,
        )
    )

    assert (
        policy.sanitize_page_title(
            " Dashboard "
        )
        == "Dashboard"
    )