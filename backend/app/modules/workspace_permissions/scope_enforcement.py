from __future__ import annotations

import uuid
from collections.abc import Iterable, Mapping
from typing import Any, TypeVar

from app.modules.workspace_permissions.access_context import (
    WorkspaceAccessContext,
)
from app.modules.workspace_permissions.scopes import (
    WorkspaceScopeType,
)


T = TypeVar("T")


def _value(
    item: object,
    name: str,
) -> Any:
    if isinstance(item, Mapping):
        return item.get(name)

    return getattr(item, name, None)


def _uuid_value(
    value: Any,
) -> uuid.UUID | None:
    if isinstance(value, uuid.UUID):
        return value

    if isinstance(value, str):
        try:
            return uuid.UUID(value)
        except ValueError:
            return None

    return None


def resolve_permission_scope(
    permission: str,
    context: WorkspaceAccessContext | None = None,
) -> WorkspaceScopeType | None:
    """
    Resolve an explicit scope name or a scoped permission.

    Unscoped permission names do not imply workspace access.
    A single granted scope can be resolved without ambiguity.
    Multiple grants are evaluated separately by filter_by_scope.
    """
    normalized = permission.strip().lower()

    try:
        return WorkspaceScopeType(normalized)
    except ValueError:
        pass

    parts = normalized.split(".")

    for scope_type in WorkspaceScopeType:
        if scope_type.value in parts:
            return scope_type

    if context is None:
        return None

    granted_types = {
        grant.type
        for grant in context.scopes
    }

    if len(granted_types) == 1:
        return next(iter(granted_types))

    return None


def _requested_scope(
    scope: WorkspaceScopeType | str,
    context: WorkspaceAccessContext,
) -> WorkspaceScopeType | None:
    if isinstance(scope, WorkspaceScopeType):
        return scope

    if isinstance(scope, str):
        return resolve_permission_scope(
            scope,
            context,
        )

    return None


def _matches_self(
    item: object,
    context: WorkspaceAccessContext,
    *,
    user_id_field: str,
    employee_id_field: str,
    employee_resource: bool,
) -> bool:
    """
    Match identities within their own namespace.

    User IDs are compared with user IDs.
    Employee IDs are compared with employee IDs.
    A resource's primary ID is used only for employee objects.
    """
    user_id = _uuid_value(
        _value(item, user_id_field)
    )

    if user_id is not None and user_id == context.user_id:
        return True

    employee_id = _uuid_value(
        _value(item, employee_id_field)
    )

    if (
        context.employee_id is not None
        and employee_id is not None
        and employee_id == context.employee_id
    ):
        return True

    if employee_resource and context.employee_id is not None:
        return (
            _uuid_value(_value(item, "id"))
            == context.employee_id
        )

    return False


def _matches_grant(
    item: object,
    context: WorkspaceAccessContext,
    grant: object,
    *,
    user_id_field: str,
    employee_id_field: str,
    company_id_field: str,
    department_id_field: str,
    team_id_field: str,
    employee_resource: bool,
) -> bool:
    scope_type = getattr(grant, "type", None)

    if scope_type == WorkspaceScopeType.WORKSPACE:
        return True

    if scope_type == WorkspaceScopeType.SELF:
        return _matches_self(
            item,
            context,
            user_id_field=user_id_field,
            employee_id_field=employee_id_field,
            employee_resource=employee_resource,
        )

    scope_fields = {
        WorkspaceScopeType.TEAM: team_id_field,
        WorkspaceScopeType.DEPARTMENT: department_id_field,
        WorkspaceScopeType.COMPANY: company_id_field,
    }

    field = scope_fields.get(scope_type)

    if field is not None:
        resource_id = _uuid_value(
            _value(item, field)
        )
        granted_id = _uuid_value(
            getattr(grant, "id", None)
        )

        return (
            resource_id is not None
            and granted_id is not None
            and resource_id == granted_id
        )

    # Shared access requires an explicit resource-specific
    # sharing policy. It never grants general employee,
    # payroll, or monitoring access here.
    return False


def filter_by_scope(
    items: Iterable[T],
    context: WorkspaceAccessContext,
    scope: WorkspaceScopeType | str | None = None,
    *,
    user_id_field: str = "user_id",
    employee_id_field: str = "employee_id",
    workspace_id_field: str = "workspace_id",
    company_id_field: str = "company_id",
    department_id_field: str = "department_id",
    team_id_field: str = "team_id",
    employee_resource: bool = False,
) -> list[T]:
    """
    Filter records using trusted context grants.

    An explicit scope restricts the grants considered.
    It cannot add a scope the context does not hold.
    Missing grants deny access.
    """
    grants = tuple(context.scopes)

    if not grants:
        return []

    if scope is not None:
        requested = _requested_scope(
            scope,
            context,
        )

        if requested is None:
            return []

        grants = tuple(
            grant
            for grant in grants
            if grant.type == requested
        )

    if not grants:
        return []

    results: list[T] = []

    for item in items:
        workspace_id = _uuid_value(
            _value(item, workspace_id_field)
        )

        if (
            workspace_id is None
            or workspace_id != context.workspace_id
        ):
            continue

        if any(
            _matches_grant(
                item,
                context,
                grant,
                user_id_field=user_id_field,
                employee_id_field=employee_id_field,
                company_id_field=company_id_field,
                department_id_field=department_id_field,
                team_id_field=team_id_field,
                employee_resource=employee_resource,
            )
            for grant in grants
        ):
            results.append(item)

    return results


def can_access_employee(
    employee: object,
    context: WorkspaceAccessContext,
    scope: WorkspaceScopeType | str | None = None,
) -> bool:
    return bool(
        filter_by_scope(
            [employee],
            context,
            scope,
            employee_resource=True,
        )
    )


def can_access_payroll(
    payroll: object,
    context: WorkspaceAccessContext,
    scope: WorkspaceScopeType | str | None = None,
) -> bool:
    return bool(
        filter_by_scope(
            [payroll],
            context,
            scope,
        )
    )


def can_access_monitoring(
    monitoring: object,
    context: WorkspaceAccessContext,
    scope: WorkspaceScopeType | str | None = None,
) -> bool:
    return bool(
        filter_by_scope(
            [monitoring],
            context,
            scope,
        )
    )


class WorkspaceScopeService:
    def __init__(
        self,
        context: WorkspaceAccessContext,
    ) -> None:
        self.context = context

    def resolve_permission_scope(
        self,
        permission: str,
    ) -> WorkspaceScopeType | None:
        return resolve_permission_scope(
            permission,
            self.context,
        )

    def filter_by_scope(
        self,
        items: Iterable[T],
        scope: WorkspaceScopeType | str | None = None,
        *,
        employee_resource: bool = False,
    ) -> list[T]:
        return filter_by_scope(
            items,
            self.context,
            scope,
            employee_resource=employee_resource,
        )

    def can_access_employee(
        self,
        employee: object,
        scope: WorkspaceScopeType | str | None = None,
    ) -> bool:
        return can_access_employee(
            employee,
            self.context,
            scope,
        )

    def can_access_payroll(
        self,
        payroll: object,
        scope: WorkspaceScopeType | str | None = None,
    ) -> bool:
        return can_access_payroll(
            payroll,
            self.context,
            scope,
        )

    def can_access_monitoring(
        self,
        monitoring: object,
        scope: WorkspaceScopeType | str | None = None,
    ) -> bool:
        return can_access_monitoring(
            monitoring,
            self.context,
            scope,
        )


__all__ = [
    "resolve_permission_scope",
    "filter_by_scope",
    "can_access_employee",
    "can_access_payroll",
    "can_access_monitoring",
    "WorkspaceScopeService",
]