from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.modules.app_tracking.schemas import (
    AppObservationRequest,
)


def test_app_observation_request_normalizes_values() -> None:
    payload = AppObservationRequest(
        process_name="  chrome.exe  ",
        executable_path=(
            "  C:\\Program Files\\Chrome\\chrome.exe  "
        ),
        window_title="  WorkforceOS  ",
        observed_at=datetime.now(
            timezone.utc
        ),
    )

    assert payload.process_name == "chrome.exe"

    assert payload.executable_path == (
        "C:\\Program Files\\Chrome\\chrome.exe"
    )

    assert payload.window_title == "WorkforceOS"


def test_app_observation_request_allows_null_optional_values() -> None:
    payload = AppObservationRequest(
        process_name="notepad.exe",
        executable_path=None,
        window_title=None,
        observed_at=datetime.now(
            timezone.utc
        ),
    )

    assert payload.executable_path is None
    assert payload.window_title is None


def test_app_observation_request_rejects_blank_process() -> None:
    with pytest.raises(
        ValidationError
    ):
        AppObservationRequest(
            process_name="   ",
            observed_at=datetime.now(
                timezone.utc
            ),
        )


def test_app_observation_request_rejects_naive_datetime() -> None:
    with pytest.raises(
        ValidationError,
        match="timezone-aware",
    ):
        AppObservationRequest(
            process_name="notepad.exe",
            observed_at=datetime(
                2026,
                8,
                28,
                12,
                0,
            ),
        )


def test_app_observation_request_forbids_unknown_fields() -> None:
    with pytest.raises(
        ValidationError
    ):
        AppObservationRequest(
            process_name="notepad.exe",
            observed_at=datetime.now(
                timezone.utc
            ),
            typed_text="should-not-be-accepted",
        )