from __future__ import annotations

from types import SimpleNamespace

from app.modules.workspace_permissions.permissions import (
    WorkspacePermission,
)
from app.modules.workspace_permissions.service import (
    WorkspacePermissionService,
)


def make_service(
) -> WorkspacePermissionService:
    return WorkspacePermissionService(
        SimpleNamespace(
            role_key="member",
        )
    )


def test_phase24_lists_member_permissions() -> None:
    service = make_service()

    permissions = service.list()

    assert (
        WorkspacePermission
        .EMPLOYEES_VIEW
        .value
        in permissions
    )


def test_phase24_checks_one_permission() -> None:
    service = make_service()

    assert service.has(
        WorkspacePermission
        .EMPLOYEES_VIEW
        .value
    )

    assert not service.has(
        WorkspacePermission
        .EMPLOYEES_MANAGE
        .value
    )


def test_phase24_checks_many_permissions() -> None:
    service = make_service()

    result = service.check_many(
        [
            WorkspacePermission
            .EMPLOYEES_VIEW
            .value,
            WorkspacePermission
            .MEETINGS_CREATE
            .value,
        ]
    )

    assert result == {
        WorkspacePermission
        .EMPLOYEES_VIEW
        .value: True,
        WorkspacePermission
        .MEETINGS_CREATE
        .value: True,
    }


def test_phase24_member_cannot_manage_employees() -> None:
    service = make_service()

    assert not service.has(
        WorkspacePermission
        .EMPLOYEES_MANAGE
        .value
    )


def test_phase24_unknown_permission_is_denied() -> None:
    service = make_service()

    assert not service.has(
        "unknown.permission"
    )
