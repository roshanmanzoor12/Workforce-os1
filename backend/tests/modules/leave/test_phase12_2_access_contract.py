from __future__ import annotations

import inspect

from app.modules.leave.access_service import (
    LeaveAccessService,
    LeaveTargetAccess,
)


def test_target_access_contract():
    fields = {
        field
        for field
        in (
            LeaveTargetAccess
            .__dataclass_fields__
        )
    }

    assert fields == {
        "actor_employee_id",
        "target_employee_id",
        "is_self",
        "is_team",
        "is_all",
    }


def test_access_service_exposes_self_resolution():
    assert hasattr(
        LeaveAccessService,
        "require_self_employee",
    )


def test_access_service_exposes_scoped_read():
    assert hasattr(
        LeaveAccessService,
        "require_leave_read",
    )


def test_access_service_exposes_approval_scope():
    assert hasattr(
        LeaveAccessService,
        "require_leave_approval",
    )


def test_access_methods_are_async():
    assert inspect.iscoroutinefunction(
        LeaveAccessService
        .require_leave_read
    )

    assert inspect.iscoroutinefunction(
        LeaveAccessService
        .require_leave_approval
    )