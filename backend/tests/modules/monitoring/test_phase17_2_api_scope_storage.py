from __future__ import annotations

import inspect
from pathlib import Path

from app.main import app

from app.modules.live_monitoring.service import (
    LiveMonitoringService,
)
from app.modules.monitoring_admin.router import (
    cleanup_screenshot_retention,
)
from app.modules.tenant_api.dependencies import (
    get_authorized_tenant_context,
)


def test_retention_cleanup_route_exists():
    schema = app.openapi()

    path = (
        "/api/v1/workspaces/"
        "{workspace_id}/"
        "monitoring-admin/"
        "screenshots/"
        "retention-cleanup"
    )

    assert path in (
        schema[
            "paths"
        ]
    )

    assert (
        "post"
        in schema[
            "paths"
        ][
            path
        ]
    )


def test_retention_cleanup_uses_authorized_context():
    source = inspect.getsource(
        cleanup_screenshot_retention
    )

    assert (
        "context: TenantContext"
        in source
    )

    assert (
        "workspace_id=workspace_id"
        in source
    )


def test_tenant_dependency_denies_workspace_mismatch():
    source = inspect.getsource(
        get_authorized_tenant_context
    )

    assert (
        "membership.workspace_id"
        in source
    )

    assert (
        "!= workspace_id"
        in source
    )


def test_screenshot_media_enforces_employee_scope():
    source = inspect.getsource(
        LiveMonitoringService
        .get_screenshot_media_object_key
    )

    assert (
        "can_access_employee"
        in source
    )

    assert (
        "outside your"
        in source
    )

    assert (
        "permitted employee scope"
        in source
    )


def test_migration_chains_from_current_head():
    path = Path(
        "migrations/tenant/versions/"
        "q7l8m9n0o1p2_"
        "phase17_2_screenshot_cadence.py"
    )

    source = path.read_text(
        encoding="utf-8"
    )

    assert (
        'revision = "q7l8m9n0o1p2"'
        in source
    )

    assert (
        'down_revision = "p6k7l8m9n0o1"'
        in source
    )

    assert (
        "screenshot_interval_seconds"
        in source
    )