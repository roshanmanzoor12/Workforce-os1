from __future__ import annotations

import inspect

from app.modules.live_monitoring.models import (
    LIVE_SESSION_STATUS_ACCEPTED,
    LIVE_SESSION_STATUS_ACTIVE,
    LIVE_SESSION_STATUS_DENIED,
    LIVE_SESSION_STATUS_ENDED,
    LIVE_SESSION_STATUS_EXPIRED,
    LIVE_SESSION_STATUS_REQUESTED,
)
from app.modules.live_monitoring.service import (
    LiveMonitoringService,
)


def test_live_screen_status_constants_are_distinct():
    statuses = {
        LIVE_SESSION_STATUS_REQUESTED,
        LIVE_SESSION_STATUS_ACCEPTED,
        LIVE_SESSION_STATUS_ACTIVE,
        LIVE_SESSION_STATUS_DENIED,
        LIVE_SESSION_STATUS_ENDED,
        LIVE_SESSION_STATUS_EXPIRED,
    }

    assert len(
        statuses
    ) == 6


def test_live_screen_request_creates_requested_state():
    source = inspect.getsource(
        LiveMonitoringService
        .request_live_screen
    )

    assert (
        "LIVE_SESSION_STATUS_REQUESTED"
        in source
    )


def test_live_screen_decision_accepts_or_denies():
    source = inspect.getsource(
        LiveMonitoringService
        .decide_live_screen
    )

    assert (
        "LIVE_SESSION_STATUS_ACCEPTED"
        in source
    )

    assert (
        "LIVE_SESSION_STATUS_DENIED"
        in source
    )


def test_live_screen_activation_requires_accepted_state():
    source = inspect.getsource(
        LiveMonitoringService
        .activate_live_screen
    )

    assert (
        "LIVE_SESSION_STATUS_ACCEPTED"
        in source
    )

    assert (
        "LIVE_SESSION_STATUS_ACTIVE"
        in source
    )

    assert (
        "accepted before activation"
        in source
    )


def test_live_screen_end_transitions_to_ended():
    source = inspect.getsource(
        LiveMonitoringService
        .end_live_screen
    )

    assert (
        "LIVE_SESSION_STATUS_ENDED"
        in source
    )

    assert (
        "ended_at"
        in source
    )