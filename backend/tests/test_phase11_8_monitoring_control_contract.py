from __future__ import annotations

from app.modules.monitoring_control.catalog import (
    MONITORING_CAPABILITY_CATALOG,
)
from app.modules.monitoring_control.permissions import (
    MONITORING_CONTROL_PERMISSIONS,
    MONITORING_LIVE_VIEW_PERMISSION,
    MONITORING_MANAGE_PERMISSION,
    MONITORING_SETTINGS_MANAGE_PERMISSION,
    MONITORING_VIEW_PERMISSION,
)
from app.modules.workspace_permissions.policy import (
    WorkspacePermissionPolicy,
)


def test_monitoring_permission_registry(
) -> None:
    assert (
        MONITORING_CONTROL_PERMISSIONS
        == {
            MONITORING_VIEW_PERMISSION,
            MONITORING_MANAGE_PERMISSION,
            MONITORING_LIVE_VIEW_PERMISSION,
            MONITORING_SETTINGS_MANAGE_PERMISSION,
        }
    )


def test_owner_has_monitoring_permissions(
) -> None:
    for permission in (
        MONITORING_CONTROL_PERMISSIONS
    ):
        assert (
            WorkspacePermissionPolicy
            .allows(
                role_key="owner",
                permission=permission,
            )
        )


def test_admin_has_monitoring_permissions(
) -> None:
    for permission in (
        MONITORING_CONTROL_PERMISSIONS
    ):
        assert (
            WorkspacePermissionPolicy
            .allows(
                role_key="admin",
                permission=permission,
            )
        )


def test_member_has_no_monitoring_control(
) -> None:
    for permission in (
        MONITORING_CONTROL_PERMISSIONS
    ):
        assert not (
            WorkspacePermissionPolicy
            .allows(
                role_key="member",
                permission=permission,
            )
        )


def test_live_screen_is_not_fake_implemented(
) -> None:
    capability = (
        MONITORING_CAPABILITY_CATALOG[
            "live_screen"
        ]
    )

    assert (
        capability["implemented"]
        is False
    )

    assert (
        capability["data_collection"]
        is False
    )


def test_control_center_does_not_collect_data(
) -> None:
    for capability in (
        MONITORING_CAPABILITY_CATALOG
        .values()
    ):
        assert (
            capability["data_collection"]
            is False
        )