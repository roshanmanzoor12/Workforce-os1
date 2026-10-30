from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationError
from app.modules.employees.models import Employee
from app.modules.workspace_permissions.permissions import (
    WorkspacePermission,
)
from app.modules.workspace_search.access import (
    resolve_search_access,
)
from app.modules.workforce_intelligence.enums import (
    IntelligenceScope,
)


@dataclass(
    frozen=True,
    slots=True,
)
class WorkforceIntelligenceAccess:
    workspace_id: uuid.UUID

    actor_user_id: uuid.UUID

    actor_employee_id: uuid.UUID | None

    scope: IntelligenceScope

    # None = every active employee in workspace.
    #
    # frozenset = only the listed employee IDs.
    employee_ids: frozenset[uuid.UUID] | None

    permissions: frozenset[str]


async def _team_employee_ids(
    *,
    session: AsyncSession,
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


async def resolve_intelligence_access(
    *,
    workspace_id: uuid.UUID,
    context: Any,
) -> WorkforceIntelligenceAccess:
    """
    Resolve the maximum Workforce Intelligence scope
    available to the current workspace actor.

    Priority:
        workspace
        -> team
        -> self

    This reuses the canonical workspace/custom-role
    permission set already resolved by workspace search.
    """

    base = await resolve_search_access(
        workspace_id=workspace_id,
        context=context,
    )

    permissions = frozenset(
        base.permissions
    )

    # =====================================================
    # WORKSPACE SCOPE
    # =====================================================

    workspace_permissions = {
        WorkspacePermission
        .ANALYTICS_ALL_READ
        .value,

        WorkspacePermission
        .PRODUCTIVITY_INSIGHTS_ALL_READ
        .value,
    }

    if not permissions.isdisjoint(
        workspace_permissions
    ):
        return WorkforceIntelligenceAccess(
            workspace_id=workspace_id,

            actor_user_id=(
                base.actor_user_id
            ),

            actor_employee_id=(
                base.actor_employee_id
            ),

            scope=(
                IntelligenceScope
                .WORKSPACE
            ),

            employee_ids=None,

            permissions=permissions,
        )

    # =====================================================
    # TEAM SCOPE
    # =====================================================

    team_permissions = {
        WorkspacePermission
        .ANALYTICS_TEAM_READ
        .value,

        WorkspacePermission
        .PRODUCTIVITY_INSIGHTS_TEAM_READ
        .value,
    }

    if not permissions.isdisjoint(
        team_permissions
    ):
        if (
            base.actor_employee_id
            is None
        ):
            raise ValidationError(
                "Employee profile required "
                "for team workforce intelligence."
            )

        if (
            base.actor_team_id
            is None
        ):
            employee_ids = frozenset(
                {
                    base.actor_employee_id,
                }
            )

        else:
            employee_ids = await (
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

        return WorkforceIntelligenceAccess(
            workspace_id=workspace_id,

            actor_user_id=(
                base.actor_user_id
            ),

            actor_employee_id=(
                base.actor_employee_id
            ),

            scope=(
                IntelligenceScope
                .TEAM
            ),

            employee_ids=(
                employee_ids
            ),

            permissions=permissions,
        )

    # =====================================================
    # SELF SCOPE
    # =====================================================

    self_permissions = {
        WorkspacePermission
        .ANALYTICS_SELF_READ
        .value,

        WorkspacePermission
        .PRODUCTIVITY_INSIGHTS_SELF_READ
        .value,
    }

    if not permissions.isdisjoint(
        self_permissions
    ):
        if (
            base.actor_employee_id
            is None
        ):
            raise ValidationError(
                "Employee profile required "
                "for self workforce intelligence."
            )

        return WorkforceIntelligenceAccess(
            workspace_id=workspace_id,

            actor_user_id=(
                base.actor_user_id
            ),

            actor_employee_id=(
                base.actor_employee_id
            ),

            scope=(
                IntelligenceScope
                .SELF
            ),

            employee_ids=frozenset(
                {
                    base.actor_employee_id,
                }
            ),

            permissions=permissions,
        )

    # =====================================================
    # DENIED
    # =====================================================

    raise ValidationError(
        "Workforce intelligence permission required."
    )


__all__ = [
    "WorkforceIntelligenceAccess",
    "resolve_intelligence_access",
]