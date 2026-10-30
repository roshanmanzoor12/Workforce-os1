from __future__ import annotations

from app.main import app
from app.modules.goals.models import Goal
from app.modules.notes.models import Note
from app.modules.workspace_permissions.permissions import (
    WorkspacePermission,
)
from app.modules.workspace_permissions.policy import (
    WorkspacePermissionPolicy,
)


def test_goal_is_tenant_model() -> None:
    assert Goal.__tablename__ == "goals"

    assert (
        "workspace_id"
        not in Goal.__table__.columns
    )


def test_note_is_tenant_model() -> None:
    assert Note.__tablename__ == "notes"

    assert (
        "workspace_id"
        not in Note.__table__.columns
    )


def test_member_has_self_permissions() -> None:
    assert (
        WorkspacePermissionPolicy
        .allows(
            role_key="member",
            permission=(
                WorkspacePermission
                .GOALS_SELF
                .value
            ),
        )
    )

    assert (
        WorkspacePermissionPolicy
        .allows(
            role_key="member",
            permission=(
                WorkspacePermission
                .NOTES_SELF
                .value
            ),
        )
    )


def test_member_has_no_admin_goal_management() -> None:
    assert not (
        WorkspacePermissionPolicy
        .allows(
            role_key="member",
            permission=(
                WorkspacePermission
                .GOALS_MANAGE
                .value
            ),
        )
    )


def test_member_has_no_admin_note_management() -> None:
    assert not (
        WorkspacePermissionPolicy
        .allows(
            role_key="member",
            permission=(
                WorkspacePermission
                .NOTES_MANAGE
                .value
            ),
        )
    )


def test_goal_routes_registered() -> None:
    paths = app.openapi()["paths"]

    required = [
        (
            "/api/v1/workspaces/"
            "{workspace_id}/goals/me"
        ),
        (
            "/api/v1/workspaces/"
            "{workspace_id}/goals/"
            "me/{goal_id}"
        ),
        (
            "/api/v1/workspaces/"
            "{workspace_id}/goals/"
            "employee/{employee_id}"
        ),
        (
            "/api/v1/workspaces/"
            "{workspace_id}/goals/{goal_id}"
        ),
    ]

    for path in required:
        assert path in paths


def test_note_routes_registered() -> None:
    paths = app.openapi()["paths"]

    required = [
        (
            "/api/v1/workspaces/"
            "{workspace_id}/notes/me"
        ),
        (
            "/api/v1/workspaces/"
            "{workspace_id}/notes/"
            "me/{note_id}"
        ),
        (
            "/api/v1/workspaces/"
            "{workspace_id}/notes/"
            "employee/{employee_id}"
        ),
        (
            "/api/v1/workspaces/"
            "{workspace_id}/notes/{note_id}"
        ),
    ]

    for path in required:
        assert path in paths