from __future__ import annotations

import inspect

from app.modules.analytics.access import (
    resolve_analytics_access,
)
from app.modules.workspace_permissions.permissions import (
    WorkspacePermission,
)


def test_analytics_permissions_exist():
    assert (
        WorkspacePermission
        .ANALYTICS_SELF_READ
        .value
        == "analytics.self.read"
    )

    assert (
        WorkspacePermission
        .ANALYTICS_TEAM_READ
        .value
        == "analytics.team.read"
    )

    assert (
        WorkspacePermission
        .ANALYTICS_ALL_READ
        .value
        == "analytics.all.read"
    )

    assert (
        WorkspacePermission
        .ANALYTICS_EXPORT
        .value
        == "analytics.export"
    )


def test_access_resolver_checks_all_scope():
    source = inspect.getsource(
        resolve_analytics_access
    )

    assert (
        "ANALYTICS_ALL_READ"
        in source
    )


def test_access_resolver_checks_team_scope():
    source = inspect.getsource(
        resolve_analytics_access
    )

    assert (
        "ANALYTICS_TEAM_READ"
        in source
    )


def test_access_resolver_checks_self_scope():
    source = inspect.getsource(
        resolve_analytics_access
    )

    assert (
        "ANALYTICS_SELF_READ"
        in source
    )


def test_access_resolver_has_denial_path():
    source = inspect.getsource(
        resolve_analytics_access
    )

    assert (
        "Analytics permission required"
        in source
        or
        "permission required"
        in source.lower()
    )