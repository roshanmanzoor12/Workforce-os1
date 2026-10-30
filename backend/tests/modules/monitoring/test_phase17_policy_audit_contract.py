from __future__ import annotations

import inspect

from app.modules.live_monitoring.phase17 import (
    record_screenshot_audit,
)
from app.modules.monitoring_admin.models import (
    MonitoringAdminPolicy,
)
from app.modules.monitoring_admin.service import (
    MonitoringAdminService,
)


def test_workspace_policy_has_screenshot_retention():
    assert hasattr(
        MonitoringAdminPolicy,
        "screenshot_retention_days",
    )


def test_policy_exposes_screenshot_retention():
    source = inspect.getsource(
        MonitoringAdminService
        .capabilities_from_policy
    )

    assert (
        "screenshot_retention_days"
        in source
    )


def test_screenshot_audit_uses_existing_audit_service():
    source = inspect.getsource(
        record_screenshot_audit
    )

    assert (
        "AuditLogService"
        in source
    )

    assert (
        "AuditEventCreate"
        in source
    )


def test_screenshot_audit_commits_control_event():
    source = inspect.getsource(
        record_screenshot_audit
    )

    assert (
        "control_session.commit"
        in source
    )

    assert (
        "control_session.rollback"
        in source
    )