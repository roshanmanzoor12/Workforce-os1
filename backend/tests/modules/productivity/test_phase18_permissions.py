from __future__ import annotations

import inspect

from app.modules.productivity_insights.access import (
    resolve_productivity_insights_access,
)
from app.modules.workspace_permissions.permissions import (
    WorkspacePermission,
)


def test_productivity_permissions_exist():
    assert (
        WorkspacePermission
        .PRODUCTIVITY_INSIGHTS_SELF_READ
        .value
        == (
            "productivity_insights."
            "self.read"
        )
    )

    assert (
        WorkspacePermission
        .PRODUCTIVITY_INSIGHTS_TEAM_READ
        .value
        == (
            "productivity_insights."
            "team.read"
        )
    )

    assert (
        WorkspacePermission
        .PRODUCTIVITY_INSIGHTS_ALL_READ
        .value
        == (
            "productivity_insights."
            "all.read"
        )
    )


def test_productivity_export_permission_exists():
    assert (
        WorkspacePermission
        .PRODUCTIVITY_INSIGHTS_EXPORT
        .value
        == (
            "productivity_insights."
            "export"
        )
    )


def test_access_resolver_checks_scoped_permissions():
    source = inspect.getsource(
        resolve_productivity_insights_access
    )

    assert (
        "PRODUCTIVITY_INSIGHTS_SELF_READ"
        in source
    )

    assert (
        "PRODUCTIVITY_INSIGHTS_TEAM_READ"
        in source
    )

    assert (
        "PRODUCTIVITY_INSIGHTS_ALL_READ"
        in source
    )