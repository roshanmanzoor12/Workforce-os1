from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import (
    select,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.core.exceptions import (
    ValidationError,
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
from app.modules.workspace_search.enums import (
    SearchEntityType,
)


@dataclass(
    frozen=True,
    slots=True,
)
class SearchAccess:
    workspace_id: uuid.UUID

    actor_user_id: uuid.UUID

    actor_employee_id: (
        uuid.UUID | None
    )

    actor_team_id: (
        uuid.UUID | None
    )

    role_key: str

    permissions: frozenset[str]

    # None means all active employees.
    #
    # A frozenset means only those employee IDs may
    # participate in employee-owned search results.
    employee_ids: (
        frozenset[uuid.UUID]
        | None
    )

    can_search_employees: bool
    can_search_goals: bool
    can_search_notes: bool
    can_search_knowledge: bool
    can_search_meetings: bool

    can_search_all_meetings: bool

    @property
    def available_types(
        self,
    ) -> list[
        SearchEntityType
    ]:
        items: list[
            SearchEntityType
        ] = []

        if self.can_search_employees:
            items.append(
                SearchEntityType.EMPLOYEE
            )

        if self.can_search_goals:
            items.append(
                SearchEntityType.GOAL
            )

        if self.can_search_notes:
            items.append(
                SearchEntityType.NOTE
            )

        if self.can_search_knowledge:
            items.append(
                SearchEntityType.KNOWLEDGE
            )

        if self.can_search_meetings:
            items.append(
                SearchEntityType.MEETING
            )

        return items


def _uuid_from_context(
    context: Any,
    name: str,
) -> uuid.UUID:
    value = getattr(
        context,
        name,
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
            f"missing {name}."
        ) from exc


def _control_session(
    context: Any,
) -> AsyncSession:
    session = getattr(
        context,
        "control_session",
        None,
    )

    if not isinstance(
        session,
        AsyncSession,
    ):
        raise ValidationError(
            "Authorized tenant context is "
            "missing control_session."
        )

    return session


def _tenant_session(
    context: Any,
) -> AsyncSession:
    session = getattr(
        context,
        "tenant_session",
        None,
    )

    if not isinstance(
        session,
        AsyncSession,
    ):
        raise ValidationError(
            "Authorized tenant context is "
            "missing tenant_session."
        )

    return session


async def _actor_employee(
    *,
    tenant_session: AsyncSession,
    actor_user_id: uuid.UUID,
) -> Employee | None:
    result = await (
        tenant_session.execute(
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

    result = await (
        tenant_session.execute(
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
    )

    ids = set(
        result
        .scalars()
        .all()
    )

    ids.add(
        employee.id
    )

    return frozenset(
        ids
    )


async def resolve_search_access(
    *,
    workspace_id: uuid.UUID,
    context: Any,
) -> SearchAccess:
    context_workspace_id = (
        _uuid_from_context(
            context,
            "workspace_id",
        )
    )

    if (
        context_workspace_id
        != workspace_id
    ):
        raise ValidationError(
            "Workspace context mismatch."
        )

    actor_user_id = (
        _uuid_from_context(
            context,
            "actor_user_id",
        )
    )

    control_session = (
        _control_session(
            context
        )
    )

    tenant_session = (
        _tenant_session(
            context
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

    permissions = frozenset(
        await (
            WorkspaceRBACService(
                control_session
            )
            .permissions_for(
                workspace_id=workspace_id,
                role_key=role_key,
            )
        )
    )

    employee = await (
        _actor_employee(
            tenant_session=tenant_session,
            actor_user_id=actor_user_id,
        )
    )

    all_employee_permission = (
        WorkspacePermission
        .EMPLOYEES_ALL_READ
        .value
        in permissions
    )

    team_employee_permission = (
        WorkspacePermission
        .EMPLOYEES_TEAM_READ
        .value
        in permissions
    )

    self_employee_permission = (
        WorkspacePermission
        .EMPLOYEES_SELF_READ
        .value
        in permissions
    )

    employee_ids: (
        frozenset[uuid.UUID]
        | None
    )

    if all_employee_permission:
        employee_ids = None

    elif (
        team_employee_permission
        and employee is not None
    ):
        employee_ids = await (
            _team_employee_ids(
                tenant_session=(
                    tenant_session
                ),
                employee=employee,
            )
        )

    elif (
        self_employee_permission
        and employee is not None
    ):
        employee_ids = frozenset(
            {
                employee.id,
            }
        )

    else:
        employee_ids = frozenset()

    can_search_employees = any(
        permission in permissions
        for permission in (
            WorkspacePermission
            .EMPLOYEES_READ
            .value,

            WorkspacePermission
            .EMPLOYEES_SELF_READ
            .value,

            WorkspacePermission
            .EMPLOYEES_TEAM_READ
            .value,

            WorkspacePermission
            .EMPLOYEES_ALL_READ
            .value,
        )
    )

    can_search_goals = any(
        permission in permissions
        for permission in (
            WorkspacePermission
            .GOALS_VIEW
            .value,

            WorkspacePermission
            .GOALS_SELF
            .value,
        )
    )

    can_search_notes = any(
        permission in permissions
        for permission in (
            WorkspacePermission
            .NOTES_VIEW
            .value,

            WorkspacePermission
            .NOTES_SELF
            .value,
        )
    )

    can_search_knowledge = any(
        permission in permissions
        for permission in (
            WorkspacePermission
            .KNOWLEDGE_VIEW
            .value,

            WorkspacePermission
            .KNOWLEDGE_SELF
            .value,
        )
    )

    can_search_meetings = any(
        permission in permissions
        for permission in (
            WorkspacePermission
            .MEETINGS_VIEW
            .value,

            WorkspacePermission
            .MEETINGS_READ
            .value,

            WorkspacePermission
            .MEETINGS_MANAGE
            .value,
        )
    )

    can_search_all_meetings = (
        WorkspacePermission
        .MEETINGS_MANAGE
        .value
        in permissions
    )

    return SearchAccess(
        workspace_id=workspace_id,

        actor_user_id=(
            actor_user_id
        ),

        actor_employee_id=(
            employee.id
            if employee is not None
            else None
        ),

        actor_team_id=(
            employee.team_id
            if employee is not None
            else None
        ),

        role_key=role_key,

        permissions=permissions,

        employee_ids=employee_ids,

        can_search_employees=(
            can_search_employees
        ),

        can_search_goals=(
            can_search_goals
        ),

        can_search_notes=(
            can_search_notes
        ),

        can_search_knowledge=(
            can_search_knowledge
        ),

        can_search_meetings=(
            can_search_meetings
        ),

        can_search_all_meetings=(
            can_search_all_meetings
        ),
    )


__all__ = [
    "SearchAccess",
    "resolve_search_access",
]