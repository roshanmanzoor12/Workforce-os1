from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import false, or_, select, true

from app.modules.employees.models import Department, Team
from app.modules.workspace_permissions.access_context import (
    WorkspaceAccessContext,
)
from app.modules.workspace_permissions.scopes import (
    WorkspaceScopeType,
)


ORGANIZATION_RESOURCES = frozenset({"departments", "teams"})


def require_organization_permission(
    context: WorkspaceAccessContext,
    *,
    resource: str,
    manage: bool = False,
) -> None:
    if resource not in ORGANIZATION_RESOURCES:
        raise ValueError(f"Unsupported organization resource: {resource}")

    permissions = (
        {f"{resource}.manage"}
        if manage
        else {f"{resource}.view", f"{resource}.read"}
    )

    if not permissions.intersection(context.permissions):
        action = "manage" if manage else "read"

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Organization {action} permission required: {resource}.",
        )

    if manage and not context.is_workspace_scoped:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Workspace scope is required to manage organization data.",
        )


def authorized_team_ids(context: WorkspaceAccessContext):
    return context.team_ids | context.scope_ids(
        WorkspaceScopeType.TEAM,
    )


def authorized_department_ids(context: WorkspaceAccessContext):
    return context.department_ids | context.scope_ids(
        WorkspaceScopeType.DEPARTMENT,
    )


def department_scope_predicate(context: WorkspaceAccessContext):
    if context.is_workspace_scoped:
        return true()

    predicates = []

    department_ids = authorized_department_ids(context)

    if department_ids:
        predicates.append(Department.id.in_(department_ids))

    team_ids = authorized_team_ids(context)

    if team_ids:
        predicates.append(
            Department.id.in_(
                select(Team.department_id).where(
                    Team.id.in_(team_ids),
                    Team.department_id.is_not(None),
                )
            )
        )

    return or_(*predicates) if predicates else false()


def team_scope_predicate(context: WorkspaceAccessContext):
    if context.is_workspace_scoped:
        return true()

    predicates = []

    team_ids = authorized_team_ids(context)

    if team_ids:
        predicates.append(Team.id.in_(team_ids))

    # Belonging to a department does not authorize every team in it.
    # An explicit department scope does.
    department_scope_ids = context.scope_ids(
        WorkspaceScopeType.DEPARTMENT,
    )

    if department_scope_ids:
        predicates.append(
            Team.department_id.in_(department_scope_ids),
        )

    return or_(*predicates) if predicates else false()


__all__ = [
    "ORGANIZATION_RESOURCES",
    "require_organization_permission",
    "authorized_team_ids",
    "authorized_department_ids",
    "department_scope_predicate",
    "team_scope_predicate",
]