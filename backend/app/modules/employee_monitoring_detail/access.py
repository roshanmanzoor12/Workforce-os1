from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select

from app.core.exceptions import (
    ValidationError,
)
from app.modules.employees.models import (
    Employee,
)
from app.modules.workspace_permissions.permissions import (
    WorkspacePermission,
)
from app.modules.workspace_search.access import (
    resolve_search_access,
)


# =========================================================
# ACCESS RESULT
# =========================================================


@dataclass(
    frozen=True,
    slots=True,
)
class EmployeeMonitoringDetailAccess:
    workspace_id: uuid.UUID

    actor_user_id: uuid.UUID

    actor_employee_id: (
        uuid.UUID
        | None
    )

    actor_team_id: (
        uuid.UUID
        | None
    )

    permissions: frozenset[str]

    visible_employee_ids: (
        frozenset[
            uuid.UUID
        ]
        | None
    )

    can_view_screens: bool


# =========================================================
# TEAM SCOPE
# =========================================================


async def _team_employee_ids(
    *,
    session,
    team_id: uuid.UUID,
    actor_employee_id: uuid.UUID,
) -> frozenset[
    uuid.UUID
]:
    result = await session.execute(
        select(
            Employee.id
        ).where(
            Employee.team_id
            == team_id,

            Employee.is_active.is_(
                True
            ),
        )
    )

    employee_ids = set(
        result.scalars().all()
    )

    employee_ids.add(
        actor_employee_id
    )

    return frozenset(
        employee_ids
    )


# =========================================================
# RESOLUTION
# =========================================================


async def resolve_employee_monitoring_detail_access(
    *,
    workspace_id: uuid.UUID,
    context: Any,
) -> EmployeeMonitoringDetailAccess:
    """
    Resolve Monitoring Detail target scope.

    MONITORING_VIEW alone opens monitoring capability surfaces,
    but does not implicitly grant access to every employee.

    Target visibility requires one of:

        monitoring.self.read
        monitoring.team.read
        monitoring.all.read
        monitoring.manage

    This preserves the architecture rule:

        effective access =
            permission
            + target scope
            + policy/entitlement
    """

    base = await resolve_search_access(
        workspace_id=workspace_id,
        context=context,
    )

    permissions = frozenset(
        base.permissions
    )

    can_manage = (
        WorkspacePermission
        .MONITORING_MANAGE
        .value
        in permissions
    )

    can_all = (
        WorkspacePermission
        .MONITORING_ALL_READ
        .value
        in permissions
    )

    can_team = (
        WorkspacePermission
        .MONITORING_TEAM_READ
        .value
        in permissions
    )

    can_self = (
        WorkspacePermission
        .MONITORING_SELF_READ
        .value
        in permissions
    )

    can_generic_view = (
        WorkspacePermission
        .MONITORING_VIEW
        .value
        in permissions
    )

    if not (
        can_manage
        or can_all
        or can_team
        or can_self
        or can_generic_view
    ):
        raise ValidationError(
            "Monitoring access required."
        )

    visible_employee_ids: (
        frozenset[
            uuid.UUID
        ]
        | None
    )

    if (
        can_manage
        or can_all
    ):
        visible_employee_ids = None

    elif (
        can_team
        and base.actor_employee_id
        is not None
    ):
        if base.actor_team_id is None:
            visible_employee_ids = (
                frozenset(
                    {
                        base.actor_employee_id,
                    }
                )
            )

        else:
            visible_employee_ids = await (
                _team_employee_ids(
                    session=(
                        context
                        .tenant_session
                    ),
                    team_id=(
                        base.actor_team_id
                    ),
                    actor_employee_id=(
                        base.actor_employee_id
                    ),
                )
            )

    elif (
        can_self
        and base.actor_employee_id
        is not None
    ):
        visible_employee_ids = (
            frozenset(
                {
                    base.actor_employee_id,
                }
            )
        )

    else:
        # Generic monitoring.view does not imply an
        # arbitrary employee target scope.
        visible_employee_ids = (
            frozenset()
        )

    can_view_screens = any(
        permission
        in permissions
        for permission in (
            WorkspacePermission
            .MONITORING_LIVE_VIEW
            .value,

            WorkspacePermission
            .MONITORING_LIVE_SCREEN
            .value,

            WorkspacePermission
            .MONITORING_MANAGE
            .value,
        )
    )

    return (
        EmployeeMonitoringDetailAccess(
            workspace_id=workspace_id,

            actor_user_id=(
                base.actor_user_id
            ),

            actor_employee_id=(
                base.actor_employee_id
            ),

            actor_team_id=(
                base.actor_team_id
            ),

            permissions=permissions,

            visible_employee_ids=(
                visible_employee_ids
            ),

            can_view_screens=(
                can_view_screens
            ),
        )
    )


# =========================================================
# TARGET AUTHORIZATION
# =========================================================


def can_access_employee(
    *,
    access: EmployeeMonitoringDetailAccess,
    employee_id: uuid.UUID,
) -> bool:
    if (
        access.visible_employee_ids
        is None
    ):
        return True

    return (
        employee_id
        in access.visible_employee_ids
    )


def require_employee_access(
    *,
    access: EmployeeMonitoringDetailAccess,
    employee_id: uuid.UUID,
) -> None:
    if can_access_employee(
        access=access,
        employee_id=employee_id,
    ):
        return

    raise ValidationError(
        "Employee is outside your "
        "permitted monitoring scope."
    )


__all__ = [
    "EmployeeMonitoringDetailAccess",
    "resolve_employee_monitoring_detail_access",
    "can_access_employee",
    "require_employee_access",
]