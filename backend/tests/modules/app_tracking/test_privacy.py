from __future__ import annotations

from app.modules.app_tracking.privacy import (
    AppTrackingPrivacyPolicy,
)


def test_window_title_is_suppressed_by_default() -> None:
    policy = AppTrackingPrivacyPolicy()

    result = policy.sanitize_window_title(
        "Secret Document - Editor"
    )

    assert result is None


def test_window_title_can_be_enabled_explicitly() -> None:
    policy = AppTrackingPrivacyPolicy(
        capture_window_titles=True
    )

    result = policy.sanitize_window_title(
        "  WorkforceOS Dashboard  "
    )

    assert result == "WorkforceOS Dashboard"


def test_window_title_is_length_bounded() -> None:
    policy = AppTrackingPrivacyPolicy(
        capture_window_titles=True,
        max_window_title_length=10,
    )

    result = policy.sanitize_window_title(
        "123456789012345"
    )

    assert result == "1234567890"


def test_blank_window_title_becomes_none() -> None:
    policy = AppTrackingPrivacyPolicy(
        capture_window_titles=True
    )

    assert (
        policy.sanitize_window_title(
            "   "
        )
        is None
    )


def test_executable_path_is_normalized() -> None:
    result = (
        AppTrackingPrivacyPolicy
        .sanitize_executable_path(
            "  C:\\Windows\\notepad.exe  "
        )
    )

    assert result == (
        "C:\\Windows\\notepad.exe"
    )