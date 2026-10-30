from __future__ import annotations

import uuid
from dataclasses import dataclass

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFound
from app.modules.workspace_permissions.permissions import (
    ALL_WORKSPACE_PERMISSIONS,
)
from app.modules.workspace_permissions.policy import (
    WorkspacePermissionPolicy,
)
from app.modules.workspace_permissions.roles import (
    BUILT_IN_ROLE_KEYS,
    OWNER_ROLE,
)
from app.modules.workspace_rbac.assignment_repository import (
    MembershipRoleAssignmentRepository,
)
from app.modules.workspace_rbac.models import WorkspaceBuiltinRoleOverride
from sqlalchemy import select
from app.modules.workspace_rbac.repository import (
    WorkspaceRBACRepository,
)
from app.modules.workspaces.models import (
    MEMBERSHIP_STATUS_ACTIVE,
)


@dataclass(frozen=True, slots=True)
class MembershipAccess:
    role_keys: tuple[str, ...]
    permissions: frozenset[str]


def _known_permissions(permissions) -> frozenset[str]:
    return frozenset(
        permission
        for permission in permissions
        if isinstance(permission, str)
        and permission in ALL_WORKSPACE_PERMISSIONS
    )


async def _resolve_role(
    repository: WorkspaceRBACRepository,
    *,
    workspace_id: uuid.UUID,
    role_key: str,
    expected_custom_role_id: uuid.UUID | None = None,
) -> frozenset[str] | None:
    """
    Return None for an unusable role.

    An active role with no permissions returns an empty frozenset.
    """
    if role_key in BUILT_IN_ROLE_KEYS:
        if expected_custom_role_id is not None:
            return None

        if role_key != OWNER_ROLE:
            override = await repository.session.scalar(
                select(WorkspaceBuiltinRoleOverride).where(
                    WorkspaceBuiltinRoleOverride.workspace_id == workspace_id,
                    WorkspaceBuiltinRoleOverride.role_key == role_key,
                )
            )
            if override is not None:
                return _known_permissions(override.permissions or [])
        return _known_permissions(
            WorkspacePermissionPolicy.permissions_for_role(role_key)
        )

    custom_role = await repository.get_custom_role_by_key(
        workspace_id=workspace_id,
        role_key=role_key,
    )

    if (
        custom_role is None
        or getattr(custom_role, "workspace_id", None) != workspace_id
        or getattr(custom_role, "role_key", None) != role_key
        or not getattr(custom_role, "is_active", False)
        or not isinstance(getattr(custom_role, "id", None), uuid.UUID)
    ):
        return None

    if (
        expected_custom_role_id is not None
        and custom_role.id != expected_custom_role_id
    ):
        return None

    permissions = await repository.get_role_permissions(custom_role.id)
    return _known_permissions(permissions)


async def resolve_membership_access(
    control_session: AsyncSession,
    *,
    workspace_id: uuid.UUID,
    membership: object,
) -> MembershipAccess:
    """
    Resolve a trusted membership's current roles and permissions.

    Only active memberships in this workspace are accepted.
    Banned memberships are rejected.
    Additional roles cannot establish workspace ownership.
    Custom roles must be active and belong to this workspace.
    Additional custom roles must match their stored role UUID.

    No records are changed and no transaction is committed.
    """
    if (
        getattr(membership, "workspace_id", None) != workspace_id
        or getattr(membership, "status", None)
        != MEMBERSHIP_STATUS_ACTIVE
    ):
        raise ResourceNotFound("Workspace was not found.")

    membership_id = getattr(membership, "id", None)

    if not isinstance(membership_id, uuid.UUID):
        raise ResourceNotFound("Workspace was not found.")

    repository = WorkspaceRBACRepository(control_session)

    moderation = await repository.get_moderation(membership_id)

    if moderation is not None and moderation.is_banned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Workspace access is banned.",
        )

    primary_role_key = getattr(membership, "role_key", None)

    if not isinstance(primary_role_key, str):
        return MembershipAccess((), frozenset())

    primary_role_key = primary_role_key.strip().lower()

    if not primary_role_key:
        return MembershipAccess((), frozenset())

    role_keys: set[str] = set()
    permissions: set[str] = set()

    primary_permissions = await _resolve_role(
        repository,
        workspace_id=workspace_id,
        role_key=primary_role_key,
    )

    if primary_permissions is not None:
        role_keys.add(primary_role_key)
        permissions.update(primary_permissions)

    # Ownership remains exclusively the membership's primary role.
    # Owners already possess the complete permission catalog.
    if primary_role_key == OWNER_ROLE:
        return MembershipAccess(
            role_keys=tuple(sorted(role_keys)),
            permissions=frozenset(permissions),
        )

    assignment_repository = MembershipRoleAssignmentRepository(
        control_session
    )

    assignments = await assignment_repository.list_for(
        workspace_id=workspace_id,
        membership_id=membership_id,
    )

    for assignment in assignments:
        if (
            getattr(assignment, "membership_id", None)
            != membership_id
        ):
            continue

        role_key = getattr(assignment, "role_key", None)

        # Stored assignments must use canonical role keys.
        if (
            not isinstance(role_key, str)
            or not role_key
            or role_key != role_key.strip().lower()
            or len(role_key) > 64
            or role_key == OWNER_ROLE
            or role_key == primary_role_key
            or role_key in role_keys
        ):
            continue

        custom_role_id = getattr(
            assignment,
            "custom_role_id",
            None,
        )

        if role_key in BUILT_IN_ROLE_KEYS:
            if custom_role_id is not None:
                continue
        elif not isinstance(custom_role_id, uuid.UUID):
            continue

        additional_permissions = await _resolve_role(
            repository,
            workspace_id=workspace_id,
            role_key=role_key,
            expected_custom_role_id=custom_role_id,
        )

        if additional_permissions is None:
            continue

        role_keys.add(role_key)
        permissions.update(additional_permissions)

    return MembershipAccess(
        role_keys=tuple(sorted(role_keys)),
        permissions=frozenset(permissions),
    )


async def resolve_membership_permissions(
    control_session: AsyncSession,
    *,
    workspace_id: uuid.UUID,
    membership: object,
) -> frozenset[str]:
    """
    Preserve the existing tenant-context resolver interface.
    """
    access = await resolve_membership_access(
        control_session,
        workspace_id=workspace_id,
        membership=membership,
    )
    return access.permissions


__all__ = [
    "MembershipAccess",
    "resolve_membership_access",
    "resolve_membership_permissions",
]