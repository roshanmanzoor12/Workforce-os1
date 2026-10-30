from __future__ import annotations

from datetime import (
    datetime,
    timedelta,
    timezone,
)
import inspect

from app.modules.live_monitoring.phase17 import (
    effective_retention_start,
)
from app.modules.live_monitoring.repository import (
    LiveMonitoringRepository,
)
from app.modules.live_monitoring.service import (
    LiveMonitoringService,
)


NOW = datetime(
    2026,
    9,
    30,
    tzinfo=timezone.utc,
)


def test_retention_window_is_backend_authoritative():
    result = effective_retention_start(
        requested_start=None,
        retention_days=30,
        now=NOW,
    )

    assert result == (
        NOW
        - timedelta(
            days=30
        )
    )


def test_requested_start_cannot_bypass_retention():
    requested = (
        NOW
        - timedelta(
            days=90
        )
    )

    result = effective_retention_start(
        requested_start=requested,
        retention_days=30,
        now=NOW,
    )

    assert result == (
        NOW
        - timedelta(
            days=30
        )
    )


def test_more_recent_requested_start_is_preserved():
    requested = (
        NOW
        - timedelta(
            days=7
        )
    )

    result = effective_retention_start(
        requested_start=requested,
        retention_days=30,
        now=NOW,
    )

    assert result == requested


def test_repository_supports_required_filters():
    signature = inspect.signature(
        LiveMonitoringRepository
        .list_screenshots_filtered
    )

    expected = {
        "employee_ids",
        "employee_id",
        "device_id",
        "status",
        "start_at",
        "end_at",
        "limit",
        "offset",
    }

    assert (
        expected
        <= set(
            signature.parameters
        )
    )


def test_service_preserves_scope_filter():
    source = inspect.getsource(
        LiveMonitoringService
        .list_screenshots_history
    )

    assert (
        "visible_employee_ids"
        in source
    )

    assert (
        "list_screenshots_filtered"
        in source
    )
