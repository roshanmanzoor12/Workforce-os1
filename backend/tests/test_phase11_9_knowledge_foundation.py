from __future__ import annotations

from pathlib import Path

from app.main import app
from app.modules.knowledge.models import (
    KnowledgeEntry,
)
from app.modules.workspace_permissions.permissions import (
    WorkspacePermission,
)
from app.modules.workspace_permissions.policy import (
    WorkspacePermissionPolicy,
)


def test_knowledge_table() -> None:
    assert (
        KnowledgeEntry.__tablename__
        == "knowledge_entries"
    )


def test_knowledge_has_primary_key() -> None:
    columns = (
        KnowledgeEntry
        .__table__
        .primary_key
        .columns
        .keys()
    )

    assert columns == [
        "id",
    ]


def test_knowledge_is_tenant_scoped() -> None:
    assert (
        "workspace_id"
        not in (
            KnowledgeEntry
            .__table__
            .columns
        )
    )


def test_knowledge_owner_fk() -> None:
    targets = {
        foreign_key.target_fullname
        for foreign_key
        in KnowledgeEntry
        .__table__
        .columns[
            "owner_employee_id"
        ]
        .foreign_keys
    }

    assert targets == {
        "employees.id",
    }


def test_member_has_knowledge_self() -> None:
    assert (
        WorkspacePermissionPolicy
        .allows(
            role_key="member",
            permission=(
                WorkspacePermission
                .KNOWLEDGE_SELF
                .value
            ),
        )
    )


def test_member_cannot_manage_knowledge() -> None:
    assert not (
        WorkspacePermissionPolicy
        .allows(
            role_key="member",
            permission=(
                WorkspacePermission
                .KNOWLEDGE_MANAGE
                .value
            ),
        )
    )


def test_admin_can_manage_knowledge() -> None:
    assert (
        WorkspacePermissionPolicy
        .allows(
            role_key="admin",
            permission=(
                WorkspacePermission
                .KNOWLEDGE_MANAGE
                .value
            ),
        )
    )


def test_self_identity_backend_derived() -> None:
    text = Path(
        "app/modules/knowledge/service.py"
    ).read_text(
        encoding="utf-8",
    )

    assert "Employee.user_id" in text
    assert "actor_user_id" in text

    assert (
        "owner_employee_id=employee.id"
        in text
    )


def test_no_database_name_from_client() -> None:
    router_text = Path(
        "app/modules/knowledge/router.py"
    ).read_text(
        encoding="utf-8",
    )

    service_text = Path(
        "app/modules/knowledge/service.py"
    ).read_text(
        encoding="utf-8",
    )

    assert (
        "database_name"
        not in router_text
    )

    assert (
        "database_name"
        not in service_text
    )


def test_knowledge_routes() -> None:
    paths = app.openapi()["paths"]

    required = [
        (
            "/api/v1/workspaces/"
            "{workspace_id}/knowledge/me"
        ),
        (
            "/api/v1/workspaces/"
            "{workspace_id}/knowledge/"
            "me/{entry_id}"
        ),
        (
            "/api/v1/workspaces/"
            "{workspace_id}/knowledge/"
            "workspace"
        ),
        (
            "/api/v1/workspaces/"
            "{workspace_id}/knowledge/"
            "{entry_id}"
        ),
    ]

    for path in required:
        assert path in paths