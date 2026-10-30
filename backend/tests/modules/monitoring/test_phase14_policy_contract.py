from __future__ import annotations

import inspect

from app.modules.monitoring_admin.service import (
    MonitoringAdminService,
)


def test_monitoring_policy_requires_disclosure():
    source = inspect.getsource(
        MonitoringAdminService.update_policy
    )

    assert (
        "disclosure_required"
        in source
    )

    assert (
        "cannot be disabled"
        in source
    )


def test_live_monitoring_policy_requires_explicit_consent():
    source = inspect.getsource(
        MonitoringAdminService.update_policy
    )

    assert (
        "explicit_live_consent_required"
        in source
    )


def test_live_monitoring_policy_requires_visible_indicator():
    source = inspect.getsource(
        MonitoringAdminService.update_policy
    )

    assert (
        "visible_live_indicator_required"
        in source
    )


def test_live_screen_checks_workspace_policy():
    source = inspect.getsource(
        MonitoringAdminService
        .require_live_screen_allowed
    )

    assert (
        "monitoring_enabled"
        in source
    )

    assert (
        "live_screen_enabled"
        in source
    )