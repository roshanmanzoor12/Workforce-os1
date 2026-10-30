from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.core.exceptions import (
    ValidationError,
)
from app.modules.analytics.access import (
    AnalyticsAccess,
    AnalyticsScope,
)
from app.modules.employees.models import (
    Employee,
)
from app.modules.memberships.repository import (
    WorkspaceMembershipRepository,
)
from app.modules.workspace_permissions.permissions import (
    WorkspacePermission,
)
from app.modules.workspace_rbac.service import (
    WorkspaceRBACService,
)


def _context_uuid(
    context: Any,
    attribute: str,
) -> uuid.UUID:
    value = getattr(
        context,
        attribute,
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
            "Authorized tenant context is "
            f"missing {attribute}."
        ) from exc


def _context_session(
    context: Any,
    attribute: str,
) -> AsyncSession:
    value = getattr(
        context,
        attribute,
        None,
    )

    if not isinstance(
        value,
        AsyncSession,
    ):
        raise ValidationError(
            "Authorized tenant context is "
            f"missing {attribute}."
        )

    return value


async def _get_actor_employee(
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


async def _get_team_employee_ids(
    *,
    tenant_session: AsyncSession,
    actor_employee: Employee,
) -> frozenset[
    uuid.UUID
]:
    if actor_employee.team_id is None:
        return frozenset(
            {
                actor_employee.id,
            }
        )

    result = await tenant_session.execute(
        select(
            Employee.id
        ).where(
            Employee.team_id
            == actor_employee.team_id,
            Employee.is_active.is_(
                True
            ),
        )
    )

    return frozenset(
        result.scalars().all()
    )


async def resolve_productivity_insights_access(
    *,
    workspace_id: uuid.UUID,
    context: Any,
) -> AnalyticsAccess:
    context_workspace_id = (
        _context_uuid(
            context,
            "workspace_id",
        )
    )

    if (
        context_workspace_id
        != workspace_id
    ):
        raise ValidationError(
            "Authorized tenant context does not "
            "match requested workspace."
        )

    actor_user_id = (
        _context_uuid(
            context,
            "actor_user_id",
        )
    )

    control_session = (
        _context_session(
            context,
            "control_session",
        )
    )

    tenant_session = (
        _context_session(
            context,
            "tenant_session",
        )
    )

    memberships = (
        WorkspaceMembershipRepository(
            control_session
        )
    )

    membership = await (
        memberships
        .get_active_for_user(
            workspace_id=workspace_id,
            user_id=actor_user_id,
        )
    )

    if membership is None:
        raise ValidationError(
            "Active workspace membership required."
        )

    role_key = (
        membership.role_key
        .strip()
        .lower()
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

    # =====================================================
    # WORKSPACE / ALL
    # =====================================================

    if (
        WorkspacePermission
        .PRODUCTIVITY_INSIGHTS_ALL_READ
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

    actor_employee = await (
        _get_actor_employee(
            tenant_session=tenant_session,
            actor_user_id=actor_user_id,
        )
    )

    # =====================================================
    # TEAM
    # =====================================================

    if (
        WorkspacePermission
        .PRODUCTIVITY_INSIGHTS_TEAM_READ
        .value
        in permissions
    ):
        employee_ids = (
            frozenset()
            if actor_employee is None
            else await (
                _get_team_employee_ids(
                    tenant_session=(
                        tenant_session
                    ),
                    actor_employee=(
                        actor_employee
                    ),
                )
            )
        )

        return AnalyticsAccess(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            role_key=role_key,
            scope=AnalyticsScope.TEAM,
            employee_ids=employee_ids,
        )

    # =====================================================
    # SELF
    # =====================================================

    if (
        WorkspacePermission
        .PRODUCTIVITY_INSIGHTS_SELF_READ
        .value
        in permissions
    ):
        employee_ids = (
            frozenset()
            if actor_employee is None
            else frozenset(
                {
                    actor_employee.id,
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
        "Productivity Insights permission required."
    )


__all__ = [
    "resolve_productivity_insights_access",
]