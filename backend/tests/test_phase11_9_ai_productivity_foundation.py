from __future__ import annotations

from pathlib import Path

from app.main import app
from app.modules.ai_productivity.enums import (
    AIProductivityAction,
    AIProviderStatus,
)
from app.modules.ai_productivity.provider import (
    DisabledAIProductivityProvider,
)
from app.modules.workspace_permissions.permissions import (
    WorkspacePermission,
)
from app.modules.workspace_permissions.policy import (
    WorkspacePermissionPolicy,
)


def test_ai_actions() -> None:
    assert {
        action.value
        for action
        in AIProductivityAction
    } == {
        "summarize_notes",
        "review_goals",
        "knowledge_assist",
        "daily_focus",
    }


def test_disabled_provider_is_safe_default() -> None:
    provider = (
        DisabledAIProductivityProvider()
    )

    info = provider.info()

    assert (
        info.status
        == AIProviderStatus.DISABLED
    )

    assert (
        info.external_processing_enabled
        is False
    )

    assert info.model_key is None


def test_member_can_use_ai_productivity() -> None:
    assert (
        WorkspacePermissionPolicy
        .allows(
            role_key="member",
            permission=(
                WorkspacePermission
                .AI_PRODUCTIVITY_USE
                .value
            ),
        )
    )


def test_member_cannot_manage_ai_productivity() -> None:
    assert not (
        WorkspacePermissionPolicy
        .allows(
            role_key="member",
            permission=(
                WorkspacePermission
                .AI_PRODUCTIVITY_MANAGE
                .value
            ),
        )
    )


def test_admin_can_manage_ai_productivity() -> None:
    assert (
        WorkspacePermissionPolicy
        .allows(
            role_key="admin",
            permission=(
                WorkspacePermission
                .AI_PRODUCTIVITY_MANAGE
                .value
            ),
        )
    )


def test_ai_routes_registered() -> None:
    paths = app.openapi()[
        "paths"
    ]

    assert (
        "/api/v1/workspaces/"
        "{workspace_id}/"
        "ai-productivity/capabilities"
        in paths
    )

    assert (
        "/api/v1/workspaces/"
        "{workspace_id}/"
        "ai-productivity/run"
        in paths
    )


def test_ai_context_is_self_scoped() -> None:
    text = Path(
        "app/modules/"
        "ai_productivity/"
        "context_service.py"
    ).read_text(
        encoding="utf-8",
    )

    assert (
        "Employee.user_id"
        in text
    )

    assert (
        "actor_user_id"
        in text
    )

    assert (
        "owner_employee_id"
        in text
    )


def test_ai_layer_does_not_accept_database_name() -> None:
    root = Path(
        "app/modules/"
        "ai_productivity"
    )

    for path in root.glob(
        "*.py"
    ):
        text = path.read_text(
            encoding="utf-8",
        )

        assert (
            "database_name"
            not in text
        )


def test_ai_layer_has_no_embedded_provider_secret() -> None:
    root = Path(
        "app/modules/"
        "ai_productivity"
    )

    forbidden = [
        "sk-",
        "api_key=",
        "authorization: bearer",
    ]

    for path in root.glob(
        "*.py"
    ):
        text = path.read_text(
            encoding="utf-8",
        ).lower()

        for token in forbidden:
            assert token not in text