from __future__ import annotations

import uuid

from fastapi import HTTPException
from sqlalchemy import false, or_, select, true

from app.modules.employees.models import (
    EMPLOYMENT_STATUS_ACTIVE,
    Employee,
)
from app.modules.projects.models import Project
from app.modules.workspace_permissions.access_context import (
    WorkspaceAccessContext,
)
from app.modules.workspace_permissions.scopes import (
    WorkspaceResourceScope,
    WorkspaceScopeType,
    self_scope,
    workspace_scope,
)
from app.modules.workspace_permissions.service import (
    WorkspacePermissionService,
)


def _active_employees():
    return select(Employee.id).where(
        Employee.is_active.is_(True),
        Employee.employment_status == EMPLOYMENT_STATUS_ACTIVE,
    )


def employee_scope_predicate(context: WorkspaceAccessContext):
    """
    Build an employee predicate for project ownership.

    The session must already belong to the authorized tenant.
    Employee and Project do not carry workspace_id columns.
    """
    conditions = []

    for grant in context.scopes:
        if grant.type == WorkspaceScopeType.WORKSPACE:
            return true()

        if grant.type == WorkspaceScopeType.SELF:
            if context.employee_id is not None:
                conditions.append(Employee.id == context.employee_id)

        elif grant.type == WorkspaceScopeType.TEAM:
            if grant.id is not None:
                conditions.append(Employee.team_id == grant.id)

        elif grant.type == WorkspaceScopeType.DEPARTMENT:
            if grant.id is not None:
                conditions.append(Employee.department_id == grant.id)

        # COMPANY has no matching column on the current Employee model.
        # SHARED is a project grant, not an employee ownership grant.

    return or_(*conditions) if conditions else false()


def project_scope_predicate(context: WorkspaceAccessContext):
    """
    Apply scope inside SQL, before counting or pagination.
    """
    if context.has_scope(WorkspaceScopeType.WORKSPACE):
        return true()

    conditions = []
    employee_conditions = employee_scope_predicate(context)

    conditions.append(
        Project.owner_employee_id.in_(
            _active_employees().where(employee_conditions)
        )
    )

    shared_ids = context.scope_ids(WorkspaceScopeType.SHARED)

    if shared_ids:
        conditions.append(Project.id.in_(shared_ids))

    return or_(*conditions)


def require_project_context(
    context: WorkspaceAccessContext,
    *,
    manage: bool = False,
) -> None:
    permission = "projects.manage" if manage else "projects.view"

    if not context.has_permission(permission):
        raise HTTPException(
            status_code=403,
            detail=f"Workspace permission required: {permission}",
        )


def validate_context_identity(
    scope,
    context: WorkspaceAccessContext,
) -> None:
    """
    A trusted access context must describe the same tenant actor.
    """
    if (
        context.workspace_id != scope.workspace_id
        or context.user_id != scope.user_id
        or context.membership_id != scope.membership_id
    ):
        raise HTTPException(
            status_code=403,
            detail="Project access context does not match tenant identity.",
        )


async def resolve_project_access(scope) -> WorkspaceAccessContext:
    """
    Build resource access from an already-authorized TenantRequestScope.

    Existing owner/admin behavior is retained. Other roles receive
    self scope. Permissions always come from WorkspacePermissionService,
    including its authoritative effective_permissions snapshot.
    """
    identifiers = (
        scope.workspace_id,
        scope.user_id,
        scope.membership_id,
    )

    if not all(isinstance(value, uuid.UUID) for value in identifiers):
        raise HTTPException(
            status_code=403,
            detail="Authorized tenant identity is unavailable.",
        )

    permission_service = WorkspacePermissionService(scope)
    permissions = frozenset(permission_service.list())

    employee_ids = list(
        (
            await scope.session.scalars(
                _active_employees().where(
                    Employee.user_id == scope.user_id
                )
            )
        ).all()
    )

    if len(employee_ids) > 1:
        raise HTTPException(
            status_code=403,
            detail="Employee identity mapping is ambiguous.",
        )

    employee_id = employee_ids[0] if employee_ids else None
    role_key = permission_service.role_key

    grants: tuple[WorkspaceResourceScope, ...] = (
        (workspace_scope(),)
        if role_key in {"owner", "admin"}
        else (self_scope(),)
    )

    return WorkspaceAccessContext(
        user_id=scope.user_id,
        workspace_id=scope.workspace_id,
        membership_id=scope.membership_id,
        employee_id=employee_id,
        role_key=role_key,
        permissions=permissions,
        scopes=grants,
    )


__all__ = [
    "employee_scope_predicate",
    "project_scope_predicate",
    "require_project_context",
    "validate_context_identity",
    "resolve_project_access",
]