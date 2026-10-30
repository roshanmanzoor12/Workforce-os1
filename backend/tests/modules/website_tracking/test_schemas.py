from __future__ import annotations

from datetime import (
    datetime,
    timezone,
)

import pytest
from pydantic import ValidationError

from app.modules.website_tracking.schemas import (
    WebsiteObservationRequest,
)


def test_observation_request_accepts_valid_payload(
) -> None:
    observed_at = datetime.now(
        timezone.utc
    )

    payload = WebsiteObservationRequest(
        browser_name="Google Chrome",
        browser_process_name="chrome.exe",
        domain="github.com",
        page_url=(
            "https://github.com/openai"
        ),
        page_title="GitHub",
        observed_at=observed_at,
    )

    assert (
        payload.browser_name
        == "Google Chrome"
    )

    assert (
        payload.browser_process_name
        == "chrome.exe"
    )

    assert payload.domain == "github.com"

    assert (
        payload.observed_at
        == observed_at
    )


def test_request_strips_required_strings(
) -> None:
    payload = WebsiteObservationRequest(
        browser_name=" Chrome ",
        browser_process_name=(
            " chrome.exe "
        ),
        domain=" github.com ",
        observed_at=datetime.now(
            timezone.utc
        ),
    )

    assert (
        payload.browser_name
        == "Chrome"
    )

    assert (
        payload.browser_process_name
        == "chrome.exe"
    )

    assert payload.domain == "github.com"


def test_optional_empty_values_become_none(
) -> None:
    payload = WebsiteObservationRequest(
        browser_name="Chrome",
        browser_process_name="chrome.exe",
        domain="github.com",
        page_url="   ",
        page_title=" ",
        observed_at=datetime.now(
            timezone.utc
        ),
    )

    assert payload.page_url is None
    assert payload.page_title is None


def test_naive_timestamp_is_rejected(
) -> None:
    with pytest.raises(
        ValidationError
    ):
        WebsiteObservationRequest(
            browser_name="Chrome",
            browser_process_name=(
                "chrome.exe"
            ),
            domain="github.com",
            observed_at=datetime.now(),
        )


def test_request_rejects_extra_fields(
) -> None:
    with pytest.raises(
        ValidationError
    ):
        WebsiteObservationRequest(
            browser_name="Chrome",
            browser_process_name=(
                "chrome.exe"
            ),
            domain="github.com",
            observed_at=datetime.now(
                timezone.utc
            ),
            employee_id="not-allowed",
        )