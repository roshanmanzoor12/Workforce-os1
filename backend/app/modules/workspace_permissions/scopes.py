from __future__ import annotations

import uuid
from dataclasses import dataclass
from enum import StrEnum


class WorkspaceScopeType(StrEnum):
    SELF = "self"
    TEAM = "team"
    DEPARTMENT = "department"
    COMPANY = "company"
    WORKSPACE = "workspace"
    SHARED = "shared"


@dataclass(
    frozen=True,
    slots=True,
)
class WorkspaceResourceScope:
    type: WorkspaceScopeType

    id: uuid.UUID | None = None

    def __post_init__(self) -> None:
        scope_type = self.type

        if isinstance(scope_type, str):
            scope_type = WorkspaceScopeType(
                scope_type.strip().lower()
            )

            object.__setattr__(
                self,
                "type",
                scope_type,
            )

        if (
            scope_type
            in {
                WorkspaceScopeType.SELF,
                WorkspaceScopeType.WORKSPACE,
            }
            and self.id is not None
        ):
            raise ValueError(
                f"{scope_type.value} scope "
                "must not contain an id."
            )

        if (
            scope_type
            in {
                WorkspaceScopeType.TEAM,
                WorkspaceScopeType.DEPARTMENT,
                WorkspaceScopeType.COMPANY,
                WorkspaceScopeType.SHARED,
            }
            and self.id is None
        ):
            raise ValueError(
                f"{scope_type.value} scope "
                "requires an id."
            )


def workspace_scope() -> WorkspaceResourceScope:
    return WorkspaceResourceScope(
        type=WorkspaceScopeType.WORKSPACE
    )


def self_scope() -> WorkspaceResourceScope:
    return WorkspaceResourceScope(
        type=WorkspaceScopeType.SELF
    )


def team_scope(
    team_id: uuid.UUID,
) -> WorkspaceResourceScope:
    return WorkspaceResourceScope(
        type=WorkspaceScopeType.TEAM,
        id=team_id,
    )


def department_scope(
    department_id: uuid.UUID,
) -> WorkspaceResourceScope:
    return WorkspaceResourceScope(
        type=WorkspaceScopeType.DEPARTMENT,
        id=department_id,
    )


def company_scope(
    company_id: uuid.UUID,
) -> WorkspaceResourceScope:
    return WorkspaceResourceScope(
        type=WorkspaceScopeType.COMPANY,
        id=company_id,
    )


__all__ = [
    "WorkspaceScopeType",
    "WorkspaceResourceScope",
    "workspace_scope",
    "self_scope",
    "team_scope",
    "department_scope",
    "company_scope",
]