from __future__ import annotations

import uuid
from dataclasses import dataclass
from enum import StrEnum

from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.core.exceptions import (
    ValidationError,
)
from app.db.tenant_dependency import (
    TenantScope,
)
from app.modules.auth.models import User
from app.modules.employees.models import (
    Employee,
)
from app.modules.workspace_permissions.permissions import (
    WorkspacePermission,
)
from app.modules.workspace_rbac.service import (
    WorkspaceRBACService,
)


class AnalyticsScope(
    StrEnum
):
    SELF = "self"
    TEAM = "team"
    ALL = "all"


@dataclass(
    frozen=True,
    slots=True,
)
class AnalyticsAccess:
    workspace_id: uuid.UUID
    actor_user_id: uuid.UUID

    role_key: str

    scope: AnalyticsScope

    employee_ids: (
        frozenset[uuid.UUID]
        | None
    )


def actor_user_id_from_scope(
    scope: TenantScope,
) -> uuid.UUID:
    value = getattr(
        scope,
        "actor_user_id",
        None,
    )

    if value is None:
        context = getattr(
            scope,
            "context",
            None,
        )

        if context is not None:
            value = getattr(
                context,
                "actor_user_id",
                None,
            )

    if value is None:
        user = getattr(
            scope,
            "user",
            None,
        )

        if user is not None:
            value = getattr(
                user,
                "id",
                None,
            )

    if isinstance(
        value,
        uuid.UUID,
    ):
        return value

    try:
        return uuid.UUID(
            str(value)
        )

    except (
        TypeError,
        ValueError,
    ) as exc:
        raise ValidationError(
            "Authenticated workspace user "
            "identity is unavailable."
        ) from exc


def role_key_from_scope(
    scope: TenantScope,
) -> str:
    value = getattr(
        scope,
        "role_key",
        None,
    )

    if value is None:
        context = getattr(
            scope,
            "context",
            None,
        )

        if context is not None:
            value = getattr(
                context,
                "role_key",
                None,
            )

    if not isinstance(
        value,
        str,
    ):
        raise ValidationError(
            "Workspace role is unavailable."
        )

    normalized = (
        value
        .strip()
        .lower()
    )

    if not normalized:
        raise ValidationError(
            "Workspace role is unavailable."
        )

    return normalized


async def _actor_employee(
    *,
    tenant_session: AsyncSession,
    actor_user_id: uuid.UUID,
) -> Employee | None:
    result = await tenant_session.execute(
        select(
            Employee
        ).where(
            Employee.user_id
            == actor_user_id,
            Employee.is_active.is_(
                True
            ),
        )
    )

    return (
        result
        .scalar_one_or_none()
    )


async def _team_employee_ids(
    *,
    tenant_session: AsyncSession,
    employee: Employee,
) -> frozenset[
    uuid.UUID
]:
    if employee.team_id is None:
        return frozenset(
            {
                employee.id,
            }
        )

    result = await tenant_session.execute(
        select(
            Employee.id
        ).where(
            Employee.team_id
            == employee.team_id,
            Employee.is_active.is_(
                True
            ),
        )
    )

    return frozenset(
        result.scalars().all()
    )


async def resolve_analytics_access(
    *,
    workspace_id: uuid.UUID,
    scope: TenantScope,
    control_session: AsyncSession,
    current_user: User,
) -> AnalyticsAccess:
    actor_user_id = (
        actor_user_id_from_scope(
            scope
        )
    )

    if actor_user_id != current_user.id:
        raise ValidationError(
            "Authenticated user does not "
            "match tenant scope."
        )

    role_key = role_key_from_scope(
        scope
    )

    rbac = WorkspaceRBACService(
        control_session
    )

    permissions = await (
        rbac.permissions_for(
            workspace_id=workspace_id,
            role_key=role_key,
        )
    )

    if (
        WorkspacePermission
        .ANALYTICS_ALL_READ
        .value
        in permissions
    ):
        return AnalyticsAccess(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            role_key=role_key,
            scope=AnalyticsScope.ALL,
            employee_ids=None,
        )

    employee = await _actor_employee(
        tenant_session=scope.session,
        actor_user_id=actor_user_id,
    )

    if (
        WorkspacePermission
        .ANALYTICS_TEAM_READ
        .value
        in permissions
    ):
        employee_ids = (
            frozenset()
            if employee is None
            else await _team_employee_ids(
                tenant_session=scope.session,
                employee=employee,
            )
        )

        return AnalyticsAccess(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            role_key=role_key,
            scope=AnalyticsScope.TEAM,
            employee_ids=employee_ids,
        )

    if (
        WorkspacePermission
        .ANALYTICS_SELF_READ
        .value
        in permissions
    ):
        employee_ids = (
            frozenset()
            if employee is None
            else frozenset(
                {
                    employee.id,
                }
            )
        )

        return AnalyticsAccess(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            role_key=role_key,
            scope=AnalyticsScope.SELF,
            employee_ids=employee_ids,
        )

    raise ValidationError(
        "Analytics permission required."
    )


__all__ = [
    "AnalyticsScope",
    "AnalyticsAccess",
    "actor_user_id_from_scope",
    "role_key_from_scope",
    "resolve_analytics_access",
]