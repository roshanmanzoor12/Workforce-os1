from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select

from app.core.exceptions import ValidationError
from app.modules.employees.models import Employee
from app.modules.workspace_permissions.permissions import (
    WorkspacePermission,
)
from app.modules.workspace_search.access import (
    resolve_search_access,
)


@dataclass(
    frozen=True,
    slots=True,
)
class DesktopAgentAccess:
    workspace_id: uuid.UUID

    actor_user_id: uuid.UUID

    actor_employee_id: uuid.UUID | None

    actor_team_id: uuid.UUID | None

    permissions: frozenset[str]

    visible_employee_ids: (
        frozenset[uuid.UUID]
        | None
    )

    can_register_self: bool

    can_manage: bool


async def _team_employee_ids(
    *,
    session,
    team_id: uuid.UUID,
    actor_employee_id: uuid.UUID,
) -> frozenset[uuid.UUID]:
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


async def resolve_desktop_agent_access(
    *,
    workspace_id: uuid.UUID,
    context: Any,
) -> DesktopAgentAccess:
    base = await resolve_search_access(
        workspace_id=workspace_id,
        context=context,
    )

    permissions = frozenset(
        base.permissions
    )

    can_manage = (
        WorkspacePermission
        .DEVICES_MANAGE
        .value
        in permissions
    )

    can_all = (
        WorkspacePermission
        .DEVICES_ALL_READ
        .value
        in permissions
    )

    can_team = (
        WorkspacePermission
        .DEVICES_TEAM_READ
        .value
        in permissions
    )

    can_self = (
        WorkspacePermission
        .DEVICES_SELF_READ
        .value
        in permissions
    )

    can_register_self = (
        can_self
        or can_team
        or can_all
        or can_manage
    )

    if can_all or can_manage:
        visible_employee_ids = None

    elif (
        can_team
        and base.actor_employee_id
        is not None
    ):
        if base.actor_team_id is None:
            visible_employee_ids = frozenset(
                {
                    base.actor_employee_id,
                }
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
        visible_employee_ids = frozenset(
            {
                base.actor_employee_id,
            }
        )

    else:
        visible_employee_ids = frozenset()

    return DesktopAgentAccess(
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

        can_register_self=(
            can_register_self
        ),

        can_manage=(
            can_manage
        ),
    )


def require_actor_employee(
    access: DesktopAgentAccess,
) -> uuid.UUID:
    if access.actor_employee_id is None:
        raise ValidationError(
            "An active employee profile is required "
            "for desktop agent registration."
        )

    return access.actor_employee_id


def can_view_employee(
    *,
    access: DesktopAgentAccess,
    employee_id: uuid.UUID,
) -> bool:
    if access.visible_employee_ids is None:
        return True

    return (
        employee_id
        in access.visible_employee_ids
    )


__all__ = [
    "DesktopAgentAccess",
    "resolve_desktop_agent_access",
    "require_actor_employee",
    "can_view_employee",
]