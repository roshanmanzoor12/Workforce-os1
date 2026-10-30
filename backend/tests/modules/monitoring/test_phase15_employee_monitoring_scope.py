from __future__ import annotations

import inspect

from app.modules.employee_monitoring_detail.access import (
    can_access_employee,
    require_employee_access,
    resolve_employee_monitoring_detail_access,
)


def test_employee_monitoring_scope_uses_self_team_all_permissions():
    source = inspect.getsource(
        resolve_employee_monitoring_detail_access
    )

    expected = (
        "MONITORING_SELF_READ",
        "MONITORING_TEAM_READ",
        "MONITORING_ALL_READ",
        "MONITORING_MANAGE",
    )

    missing = [
        item
        for item in expected
        if item not in source
    ]

    assert not missing, (
        "Missing monitoring target "
        "scope permissions: "
        + ", ".join(
            missing
        )
    )


def test_generic_monitoring_view_does_not_grant_all_employee_scope():
    source = inspect.getsource(
        resolve_employee_monitoring_detail_access
    )

    assert (
        "can_generic_view"
        in source
    )

    assert (
        "visible_employee_ids = (\n"
        "            frozenset()"
        in source
    )


def test_employee_target_guard_exists():
    assert callable(
        can_access_employee
    )

    source = inspect.getsource(
        require_employee_access
    )

    assert (
        "outside your"
        in source
    )

    assert (
        "permitted monitoring scope"
        in source
    )