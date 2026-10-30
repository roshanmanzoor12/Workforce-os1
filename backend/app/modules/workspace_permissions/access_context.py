from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from app.modules.workspace_permissions.scopes import (
    WorkspaceResourceScope,
    WorkspaceScopeType,
)


@dataclass(
    frozen=True,
    slots=True,
)
class WorkspaceAccessContext:
    user_id: uuid.UUID

    workspace_id: uuid.UUID

    membership_id: uuid.UUID

    employee_id: uuid.UUID | None

    role_key: str

    permissions: frozenset[str]

    scopes: tuple[
        WorkspaceResourceScope,
        ...,
    ]

    department_ids: frozenset[
        uuid.UUID
    ] = frozenset()

    team_ids: frozenset[
        uuid.UUID
    ] = frozenset()

    managed_membership_ids: frozenset[
        uuid.UUID
    ] = frozenset()

    workspace_entitlements: dict[
        str,
        Any,
    ] | None = None

    company_ids: frozenset[
        uuid.UUID
    ] = frozenset()

    def has_permission(
        self,
        permission: str,
    ) -> bool:
        normalized = permission.strip().lower()

        return normalized in {
            item.strip().lower()
            for item in self.permissions
        }

    def has_scope(
        self,
        scope_type: WorkspaceScopeType,
    ) -> bool:
        return any(
            item.type == scope_type
            for item in self.scopes
        )

    def scope_ids(
        self,
        scope_type: WorkspaceScopeType,
    ) -> frozenset[uuid.UUID]:
        return frozenset(
            item.id
            for item in self.scopes
            if (
                item.type == scope_type
                and item.id is not None
            )
        )

    @property
    def is_workspace_scoped(
        self,
    ) -> bool:
        return self.has_scope(
            WorkspaceScopeType.WORKSPACE
        )


__all__ = [
    "WorkspaceAccessContext",
]