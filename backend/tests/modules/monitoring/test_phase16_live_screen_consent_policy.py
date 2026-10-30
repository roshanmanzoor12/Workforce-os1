from __future__ import annotations

import inspect

from app.modules.live_monitoring.service import (
    LiveMonitoringService,
)
from app.modules.monitoring_admin.service import (
    MonitoringAdminService,
)


def test_request_requires_live_screen_permission():
    source = inspect.getsource(
        LiveMonitoringService
        .request_live_screen
    )

    assert (
        "can_request_live_screen"
        in source
    )

    assert (
        "Live screen permission required"
        in source
    )


def test_decision_requires_visible_indicator_on_accept():
    source = inspect.getsource(
        LiveMonitoringService
        .decide_live_screen
    )

    assert (
        "visible_indicator_shown"
        in source
    )

    assert (
        "must be shown before acceptance"
        in source
    )


def test_workspace_policy_requires_explicit_consent():
    source = inspect.getsource(
        MonitoringAdminService
        .require_live_screen_allowed
    )

    assert (
        "explicit_live_consent_required"
        in source
    )

    assert (
        "explicit consent is required"
        in source
    )


def test_workspace_policy_requires_visible_indicator():
    source = inspect.getsource(
        MonitoringAdminService
        .require_live_screen_allowed
    )

    assert (
        "visible_live_indicator_required"
        in source
    )

    assert (
        "visible indicator is required"
        in source
    )


def test_sensitive_policy_cannot_disable_consent():
    source = inspect.getsource(
        MonitoringAdminService
        .update_policy
    )

    assert (
        "cannot be disabled"
        in source
    )

    assert (
        "explicit_live_consent_required"
        in source
    )

    assert (
        "visible_live_indicator_required"
        in source
    )