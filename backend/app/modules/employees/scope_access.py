from __future__ import annotations

import uuid

from fastapi import HTTPException
from sqlalchemy import false, or_, select, true

from app.modules.employees.models import (
    EMPLOYMENT_STATUS_ACTIVE,
    Employee,
)
from app.modules.workspace_permissions.access_context import (
    WorkspaceAccessContext,
)
from app.modules.workspace_permissions.request_scopes import (
    resolve_request_saved_scopes,
)
from app.modules.workspace_permissions.scopes import (
    WorkspaceResourceScope,
    WorkspaceScopeType,
)
from app.modules.workspace_permissions.service import (
    WorkspacePermissionService,
)


EMPLOYEE_READ_PERMISSIONS = frozenset({
    "employees.view",
    "employees.read",
    "employees.self.read",
    "employees.team.read",
    "employees.all.read",
})

EMPLOYEE_PROFILE_FIELDS = frozenset({
    "first_name",
    "last_name",
    "phone_number",
    "avatar_url",
})


def require_employee_read(context: WorkspaceAccessContext) -> None:
    if context.permissions.intersection(EMPLOYEE_READ_PERMISSIONS):
        return

    raise HTTPException(
        status_code=403,
        detail="Employee read permission required.",
    )


def require_employee_action(
    context: WorkspaceAccessContext,
    action: str,
) -> None:
    if action not in {"create", "update", "delete"}:
        raise ValueError("Unsupported employee action.")

    accepted = {
        "employees.manage",
        f"employees.{action}",
    }

    if context.permissions.intersection(accepted):
        return

    raise HTTPException(
        status_code=403,
        detail=f"Employee {action} permission required.",
    )


def require_employee_workspace_scope(
    context: WorkspaceAccessContext,
) -> None:
    if context.is_workspace_scoped:
        return

    raise HTTPException(
        status_code=403,
        detail="Workspace-wide employee scope required.",
    )


def require_employee_update_fields(
    context: WorkspaceAccessContext,
    fields: set[str],
) -> None:
    if context.is_workspace_scoped:
        return

    if fields.issubset(EMPLOYEE_PROFILE_FIELDS):
        return

    raise HTTPException(
        status_code=403,
        detail=(
            "Changing employee identity, organization, or employment "
            "requires workspace-wide employee scope."
        ),
    )


def employee_scope_predicate(context: WorkspaceAccessContext):
    if context.is_workspace_scoped:
        return true()

    predicates = []

    for grant in context.scopes:
        if grant.type == WorkspaceScopeType.SELF:
            if context.employee_id is not None:
                predicates.append(Employee.id == context.employee_id)

        elif grant.type == WorkspaceScopeType.TEAM:
            if grant.id is not None:
                predicates.append(Employee.team_id == grant.id)

        elif grant.type == WorkspaceScopeType.DEPARTMENT:
            if grant.id is not None:
                predicates.append(Employee.department_id == grant.id)

    return or_(*predicates) if predicates else false()


def can_access_employee_row(
    context: WorkspaceAccessContext,
    employee: object,
) -> bool:
    if context.is_workspace_scoped:
        return True

    for grant in context.scopes:
        if grant.type == WorkspaceScopeType.SELF:
            if (
                context.employee_id is not None
                and getattr(employee, "id", None) == context.employee_id
            ):
                return True

        elif grant.type == WorkspaceScopeType.TEAM:
            if (
                grant.id is not None
                and getattr(employee, "team_id", None) == grant.id
            ):
                return True

        elif grant.type == WorkspaceScopeType.DEPARTMENT:
            if (
                grant.id is not None
                and getattr(employee, "department_id", None) == grant.id
            ):
                return True

    return False


def build_employee_access(
    scope: object,
    employee: object | None,
) -> WorkspaceAccessContext:
    identity = {}

    for name in ("workspace_id", "user_id", "membership_id"):
        value = getattr(scope, name, None)

        if not isinstance(value, uuid.UUID):
            raise HTTPException(
                status_code=403,
                detail="Authorized employee scope is unavailable.",
            )

        identity[name] = value

    permission_service = WorkspacePermissionService(scope)
    permissions = frozenset(permission_service.list())

    employee_id = None
    team_id = None
    department_id = None

    if employee is not None:
        if (
            getattr(employee, "user_id", None) != identity["user_id"]
            or getattr(employee, "is_active", None) is not True
            or getattr(employee, "employment_status", None)
            != EMPLOYMENT_STATUS_ACTIVE
            or not isinstance(getattr(employee, "id", None), uuid.UUID)
        ):
            raise HTTPException(
                status_code=403,
                detail="Employee identity does not match the caller.",
            )

        employee_id = employee.id

        candidate_team = getattr(employee, "team_id", None)
        candidate_department = getattr(employee, "department_id", None)

        if isinstance(candidate_team, uuid.UUID):
            team_id = candidate_team

        if isinstance(candidate_department, uuid.UUID):
            department_id = candidate_department

    scopes = []

    if "employees.all.read" in permissions:
        scopes.append(
            WorkspaceResourceScope(WorkspaceScopeType.WORKSPACE)
        )
    else:
        if employee_id is not None:
            scopes.append(
                WorkspaceResourceScope(WorkspaceScopeType.SELF)
            )

        if (
            "employees.team.read" in permissions
            and team_id is not None
        ):
            scopes.append(
                WorkspaceResourceScope(
                    WorkspaceScopeType.TEAM,
                    team_id,
                )
            )

    return WorkspaceAccessContext(
        user_id=identity["user_id"],
        workspace_id=identity["workspace_id"],
        membership_id=identity["membership_id"],
        employee_id=employee_id,
        role_key=permission_service.role_key,
        permissions=permissions,
        scopes=tuple(scopes),
        team_ids=(
            frozenset({team_id})
            if team_id is not None
            else frozenset()
        ),
        department_ids=(
            frozenset({department_id})
            if department_id is not None
            else frozenset()
        ),
    )


async def resolve_employee_access(
    scope: object,
) -> WorkspaceAccessContext:
    user_id = getattr(scope, "user_id", None)

    if not isinstance(user_id, uuid.UUID):
        raise HTTPException(
            status_code=403,
            detail="Authorized employee identity is unavailable.",
        )

    statement = select(Employee).where(
        Employee.user_id == user_id,
        Employee.is_active.is_(True),
        Employee.employment_status == EMPLOYMENT_STATUS_ACTIVE,
    )

    result = await scope.session.execute(statement)
    employees = result.scalars().all()

    if len(employees) > 1:
        raise HTTPException(
            status_code=403,
            detail="Employee identity is ambiguous.",
        )

    employee = employees[0] if employees else None
    context = build_employee_access(scope, employee)

    return await resolve_request_saved_scopes(
        scope,
        context,
    )


__all__ = [
    "EMPLOYEE_READ_PERMISSIONS",
    "EMPLOYEE_PROFILE_FIELDS",
    "require_employee_read",
    "require_employee_action",
    "require_employee_workspace_scope",
    "require_employee_update_fields",
    "employee_scope_predicate",
    "can_access_employee_row",
    "build_employee_access",
    "resolve_employee_access",
]