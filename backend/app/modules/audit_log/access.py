from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.core.exceptions import (
    ValidationError,
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


@dataclass(
    frozen=True,
    slots=True,
)
class AuditAccess:
    workspace_id: uuid.UUID

    actor_user_id: uuid.UUID

    role_key: str

    permissions: frozenset[str]


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


def _control_session(
    context: Any,
) -> AsyncSession:
    value = getattr(
        context,
        "control_session",
        None,
    )

    if not isinstance(
        value,
        AsyncSession,
    ):
        raise ValidationError(
            "Authorized tenant context is "
            "missing control_session."
        )

    return value


async def resolve_audit_access(
    *,
    workspace_id: uuid.UUID,
    context: Any,
) -> AuditAccess:
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
        _control_session(
            context
        )
    )

    membership_repository = (
        WorkspaceMembershipRepository(
            control_session
        )
    )

    membership = await (
        membership_repository
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

    permissions = frozenset(
        await rbac.permissions_for(
            workspace_id=workspace_id,
            role_key=role_key,
        )
    )

    required = {
        WorkspacePermission
        .AUDIT_READ
        .value,

        WorkspacePermission
        .AUDIT_VIEW
        .value,
    }

    if permissions.isdisjoint(
        required
    ):
        raise ValidationError(
            "Audit log permission required."
        )

    return AuditAccess(
        workspace_id=workspace_id,
        actor_user_id=actor_user_id,
        role_key=role_key,
        permissions=permissions,
    )


__all__ = [
    "AuditAccess",
    "resolve_audit_access",
]