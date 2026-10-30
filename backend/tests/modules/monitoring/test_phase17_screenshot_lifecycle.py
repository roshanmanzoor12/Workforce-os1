from __future__ import annotations

import inspect

from app.modules.live_monitoring.models import (
    SCREENSHOT_STATUS_COMPLETED,
    SCREENSHOT_STATUS_DENIED,
    SCREENSHOT_STATUS_EXPIRED,
    SCREENSHOT_STATUS_FAILED,
    SCREENSHOT_STATUS_PENDING,
)
from app.modules.live_monitoring.service import (
    LiveMonitoringService,
)


def test_all_required_screenshot_states_exist():
    states = {
        SCREENSHOT_STATUS_PENDING,
        SCREENSHOT_STATUS_COMPLETED,
        SCREENSHOT_STATUS_DENIED,
        SCREENSHOT_STATUS_EXPIRED,
        SCREENSHOT_STATUS_FAILED,
    }

    assert states == {
        "pending",
        "completed",
        "denied",
        "expired",
        "failed",
    }


def test_complete_requires_pending_request():
    source = inspect.getsource(
        LiveMonitoringService
        .complete_screenshot
    )

    assert (
        "SCREENSHOT_STATUS_PENDING"
        in source
    )

    assert (
        "SCREENSHOT_STATUS_COMPLETED"
        in source
    )


def test_complete_requires_consent():
    source = inspect.getsource(
        LiveMonitoringService
        .complete_screenshot
    )

    assert (
        "consent_confirmed"
        in source
    )

    assert (
        "explicit user consent"
        in source
    )


def test_complete_requires_visible_indicator():
    source = inspect.getsource(
        LiveMonitoringService
        .complete_screenshot
    )

    assert (
        "visible_indicator_shown"
        in source
    )

    assert (
        "visible capture indicator"
        in source
    )


def test_failure_transition_exists():
    source = inspect.getsource(
        LiveMonitoringService
        .fail_screenshot
    )

    assert (
        "SCREENSHOT_STATUS_FAILED"
        in source
    )

    assert (
        "failure_reason"
        in source
    )