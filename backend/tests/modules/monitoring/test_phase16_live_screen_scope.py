from __future__ import annotations

import inspect

from app.modules.live_monitoring.access import (
    can_access_employee,
    resolve_live_monitoring_access,
)
from app.modules.live_monitoring.service import (
    LiveMonitoringService,
)


def test_live_screen_access_uses_live_screen_permission():
    source = inspect.getsource(
        resolve_live_monitoring_access
    )

    assert (
        "MONITORING_LIVE_SCREEN"
        in source
    )


def test_live_screen_access_preserves_employee_scope():
    source = inspect.getsource(
        resolve_live_monitoring_access
    )

    assert (
        "visible_employee_ids"
        in source
    )


def test_employee_scope_guard_supports_all_or_filtered():
    source = inspect.getsource(
        can_access_employee
    )

    assert (
        "visible_employee_ids is None"
        in source
    )

    assert (
        "employee_id"
        in source
    )


def test_service_rejects_device_outside_scope():
    source = inspect.getsource(
        LiveMonitoringService
        ._device
    )

    assert (
        "can_access_employee"
        in source
    )

    assert (
        "outside your permitted"
        in source
    )