from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ConflictError,
    ResourceNotFound,
    ValidationError,
)
from app.modules.auth.models import User
from app.modules.workspace_permissions.effective import (
    MembershipAccess,
    resolve_membership_access,
)
from app.modules.workspace_permissions.permissions import (
    ALL_WORKSPACE_PERMISSIONS,
    WorkspacePermission,
)
from app.modules.workspace_permissions.policy import WorkspacePermissionPolicy
from app.modules.workspace_permissions.roles import (
    BUILT_IN_ROLE_KEYS,
    ROLE_DISPLAY_NAMES,
)
from app.modules.workspace_rbac.assignment_models import (
    WorkspaceMembershipRoleAssignment,
)
from app.modules.workspace_rbac.assignment_repository import (
    MembershipRoleAssignmentRepository,
)
from app.modules.workspace_rbac.models import WorkspaceBuiltinRoleOverride
from app.modules.workspace_rbac.repository import WorkspaceRBACRepository
from app.modules.workspace_rbac.schemas import (
    PermissionCatalogResponse,
    WorkspaceBootstrapResponse,
    WorkspaceMemberListResponse,
    WorkspaceMemberModerationPublic,
    WorkspaceMemberPublic,
    WorkspaceMemberRoleUpdateRequest,
    WorkspaceMemberRolesResponse,
    WorkspaceMemberVisibilityRequest,
    WorkspaceModerationActionResponse,
    WorkspaceRoleCreateRequest,
    WorkspaceRoleListResponse,
    WorkspaceRolePublic,
    WorkspaceRoleUpdateRequest,
)
from app.modules.workspaces.models import (
    MEMBERSHIP_STATUS_ACTIVE,
    MEMBERSHIP_STATUS_REMOVED,
    MEMBERSHIP_STATUS_SUSPENDED,
    WORKSPACE_ROLE_OWNER,
    WORKSPACE_STATUS_READY,
    Workspace,
)
from app.modules.workspaces.repository import WorkspaceRepository


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class WorkspaceRBACService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = WorkspaceRBACRepository(session)
        self.workspace_repository = WorkspaceRepository(session)
        self.assignment_repository = MembershipRoleAssignmentRepository(session)

    async def _workspace(
        self,
        workspace_id: uuid.UUID,
        *,
        lock: bool = False,
    ):
        statement = select(Workspace).where(Workspace.id == workspace_id)

        if lock:
            statement = statement.with_for_update()

        workspace = await self.session.scalar(
            statement.execution_options(populate_existing=True)
        )

        if (
            workspace is None
            or workspace.id != workspace_id
            or not workspace.is_active
            or workspace.status != WORKSPACE_STATUS_READY
        ):
            raise ResourceNotFound("Workspace was not found.")

        return workspace

    async def _actor_membership(
        self,
        *,
        workspace_id: uuid.UUID,
        user: User,
    ):
        await self._workspace(workspace_id)

        membership = (
            await self.workspace_repository.get_active_workspace_membership(
                workspace_id=workspace_id,
                user_id=user.id,
            )
        )

        if (
            membership is None
            or membership.workspace_id != workspace_id
            or membership.user_id != user.id
            or membership.status != MEMBERSHIP_STATUS_ACTIVE
        ):
            raise ResourceNotFound("Workspace was not found.")

        moderation = await self.repository.get_moderation(membership.id)

        if moderation is not None and moderation.is_banned:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Workspace access is banned.",
            )

        return membership

    async def _access(self, membership):
        return await resolve_membership_access(
            self.session,
            workspace_id=membership.workspace_id,
            membership=membership,
        )

    async def _member_access(self, membership):
        if membership.status != MEMBERSHIP_STATUS_ACTIVE:
            return MembershipAccess((), frozenset())

        moderation = await self.repository.get_moderation(membership.id)

        if moderation is not None and moderation.is_banned:
            return MembershipAccess((), frozenset())

        return await self._access(membership)

    async def _built_in_permissions(self, workspace_id: uuid.UUID, role_key: str) -> frozenset[str]:
        if role_key == WORKSPACE_ROLE_OWNER:
            return frozenset(ALL_WORKSPACE_PERMISSIONS)
        override = await self.session.scalar(
            select(WorkspaceBuiltinRoleOverride).where(
                WorkspaceBuiltinRoleOverride.workspace_id == workspace_id,
                WorkspaceBuiltinRoleOverride.role_key == role_key,
            )
        )
        if override is not None:
            return frozenset(key for key in (override.permissions or []) if key in ALL_WORKSPACE_PERMISSIONS)
        return frozenset(WorkspacePermissionPolicy.permissions_for_role(role_key))

    async def update_builtin_role(
        self, *, workspace_id: uuid.UUID, role_key: str,
        permissions: list[str], user: User,
    ) -> WorkspaceRolePublic:
        """Replace one workspace's non-owner role policy atomically."""
        normalized = role_key.strip().lower()
        if normalized not in BUILT_IN_ROLE_KEYS or normalized == WORKSPACE_ROLE_OWNER:
            raise ValidationError("Owner or unknown built-in role cannot be edited.")
        requested = set(permissions)
        unknown = requested - ALL_WORKSPACE_PERMISSIONS
        if unknown:
            raise ValidationError("Unknown permissions: " + ", ".join(sorted(unknown)))
        try:
            actor = await self._require(
                workspace_id=workspace_id, user=user,
                permission=WorkspacePermission.ROLES_MANAGE.value,
            )
            # Only a primary owner may alter system role policies.
            if actor.role_key != WORKSPACE_ROLE_OWNER:
                raise HTTPException(status_code=403, detail="Workspace owner required to edit built-in roles.")
            await self._assert_grantable(actor, requested)
            override = await self.session.scalar(
                select(WorkspaceBuiltinRoleOverride).where(
                    WorkspaceBuiltinRoleOverride.workspace_id == workspace_id,
                    WorkspaceBuiltinRoleOverride.role_key == normalized,
                ).with_for_update()
            )
            if override is None:
                override = WorkspaceBuiltinRoleOverride(
                    workspace_id=workspace_id, role_key=normalized,
                    permissions=sorted(requested),
                )
                self.session.add(override)
            else:
                override.permissions = sorted(requested)
            await self.session.commit()
            return WorkspaceRolePublic(
                id=None, role_key=normalized,
                display_name=ROLE_DISPLAY_NAMES[normalized], description=None,
                permissions=sorted(requested), is_builtin=True,
                is_immutable=False, is_active=True,
            )
        except Exception:
            await self.session.rollback()
            raise

    async def permissions_for(
        self,
        *,
        workspace_id: uuid.UUID,
        role_key: str,
    ) -> frozenset[str]:
        normalized = role_key.strip().lower()

        if normalized in BUILT_IN_ROLE_KEYS:
            return await self._built_in_permissions(workspace_id, normalized)

        custom = await self.repository.get_custom_role_by_key(
            workspace_id=workspace_id,
            role_key=normalized,
        )

        if (
            custom is None
            or custom.workspace_id != workspace_id
            or custom.role_key != normalized
            or not custom.is_active
        ):
            return frozenset()

        permissions = await self.repository.get_role_permissions(custom.id)

        return frozenset(
            permission
            for permission in permissions
            if permission in ALL_WORKSPACE_PERMISSIONS
        )

    async def _require(
        self,
        *,
        workspace_id: uuid.UUID,
        user: User,
        permission: str,
    ):
        await self._workspace(workspace_id, lock=True)

        membership = await self._actor_membership(
            workspace_id=workspace_id,
            user=user,
        )
        access = await self._access(membership)

        if permission not in access.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Workspace permission required: {permission}",
            )

        return membership

    async def _assert_grantable(self, actor, permissions):
        requested = frozenset(permissions)
        unknown = requested - ALL_WORKSPACE_PERMISSIONS

        if unknown:
            raise ValidationError(
                "Unknown permissions: " + ", ".join(sorted(unknown))
            )

        access = await self._access(actor)

        if not requested.issubset(access.permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "You cannot grant or manage permissions "
                    "you do not possess."
                ),
            )

    async def _target(
        self,
        *,
        workspace_id: uuid.UUID,
        membership_id: uuid.UUID,
    ):
        membership = await self.repository.get_membership(
            workspace_id=workspace_id,
            membership_id=membership_id,
        )

        if (
            membership is None
            or membership.workspace_id != workspace_id
            or membership.id != membership_id
        ):
            raise ResourceNotFound("Workspace membership was not found.")

        return membership

    async def _assignment_permissions(
        self,
        *,
        workspace_id: uuid.UUID,
        role_key: str,
        allow_inactive: bool = False,
    ):
        if role_key in BUILT_IN_ROLE_KEYS:
            return await self._built_in_permissions(workspace_id, role_key)

        role = await self.repository.get_custom_role_by_key(
            workspace_id=workspace_id,
            role_key=role_key,
        )

        if (
            role is None
            or role.workspace_id != workspace_id
            or role.role_key != role_key
            or (not allow_inactive and not role.is_active)
        ):
            raise ResourceNotFound("Workspace role was not found.")

        permissions = await self.repository.get_role_permissions(role.id)

        return frozenset(
            permission
            for permission in permissions
            if permission in ALL_WORKSPACE_PERMISSIONS
        )

    async def _member_roles_response(self, membership):
        rows = await self.assignment_repository.list_for(
            workspace_id=membership.workspace_id,
            membership_id=membership.id,
        )
        access = await self._member_access(membership)

        return WorkspaceMemberRolesResponse(
            workspace_id=membership.workspace_id,
            membership_id=membership.id,
            primary_role_key=membership.role_key,
            additional_role_keys=sorted({row.role_key for row in rows}),
            effective_role_keys=list(access.role_keys),
            permissions=sorted(access.permissions),
        )

    async def permission_catalog(
        self,
        *,
        workspace_id: uuid.UUID,
        user: User,
    ) -> PermissionCatalogResponse:
        await self._actor_membership(workspace_id=workspace_id, user=user)

        return PermissionCatalogResponse(
            permissions=sorted(ALL_WORKSPACE_PERMISSIONS)
        )

    async def list_roles(
        self,
        *,
        workspace_id: uuid.UUID,
        user: User,
    ) -> WorkspaceRoleListResponse:
        await self._actor_membership(workspace_id=workspace_id, user=user)

        items: list[WorkspaceRolePublic] = []

        for role_key in sorted(BUILT_IN_ROLE_KEYS):
            permissions = await self._built_in_permissions(workspace_id, role_key)

            items.append(
                WorkspaceRolePublic(
                    id=None,
                    role_key=role_key,
                    display_name=ROLE_DISPLAY_NAMES[role_key],
                    description=None,
                    permissions=sorted(permissions),
                    is_builtin=True,
                    is_immutable=role_key == WORKSPACE_ROLE_OWNER,
                    is_active=True,
                )
            )

        custom_roles = await self.repository.list_custom_roles(workspace_id)

        for role in custom_roles:
            permissions = await self.repository.get_role_permissions(role.id)

            items.append(
                WorkspaceRolePublic(
                    id=role.id,
                    role_key=role.role_key,
                    display_name=role.display_name,
                    description=role.description,
                    permissions=sorted(permissions),
                    is_builtin=False,
                    is_immutable=False,
                    is_active=role.is_active,
                )
            )

        return WorkspaceRoleListResponse(roles=items)

    async def create_role(
        self,
        payload: WorkspaceRoleCreateRequest,
        *,
        workspace_id: uuid.UUID,
        user: User,
    ) -> WorkspaceRolePublic:
        try:
            actor = await self._require(
                workspace_id=workspace_id,
                user=user,
                permission=WorkspacePermission.ROLES_MANAGE.value,
            )

            if payload.role_key in BUILT_IN_ROLE_KEYS:
                raise ConflictError("Built-in role key cannot be reused.")

            existing = await self.repository.get_custom_role_by_key(
                workspace_id=workspace_id,
                role_key=payload.role_key,
            )

            if existing:
                raise ConflictError("Role key already exists.")

            permissions = set(payload.permissions)
            unknown = permissions - ALL_WORKSPACE_PERMISSIONS

            if unknown:
                raise ValidationError(
                    "Unknown permissions: " + ", ".join(sorted(unknown))
                )

            await self._assert_grantable(actor, permissions)

            role = await self.repository.create_custom_role(
                workspace_id=workspace_id,
                role_key=payload.role_key,
                display_name=payload.display_name,
                description=payload.description,
                created_by_user_id=user.id,
            )

            await self.repository.set_role_permissions(
                role_id=role.id,
                permissions=permissions,
            )
            await self.session.commit()

            return WorkspaceRolePublic(
                id=role.id,
                role_key=role.role_key,
                display_name=role.display_name,
                description=role.description,
                permissions=sorted(permissions),
                is_builtin=False,
                is_immutable=False,
                is_active=True,
            )

        except Exception:
            await self.session.rollback()
            raise

    async def update_role(
        self,
        payload: WorkspaceRoleUpdateRequest,
        *,
        workspace_id: uuid.UUID,
        role_id: uuid.UUID,
        user: User,
    ) -> WorkspaceRolePublic:
        try:
            actor = await self._require(
                workspace_id=workspace_id,
                user=user,
                permission=WorkspacePermission.ROLES_MANAGE.value,
            )

            role = await self.repository.get_custom_role(
                workspace_id=workspace_id,
                role_id=role_id,
            )

            if role is None:
                raise ResourceNotFound(
                    "Custom workspace role was not found."
                )

            proposed_permissions = (
                set(payload.permissions)
                if payload.permissions is not None
                else await self.repository.get_role_permissions(role.id)
            )

            await self._assert_grantable(actor, proposed_permissions)

            if payload.display_name is not None:
                role.display_name = payload.display_name

            if payload.description is not None:
                role.description = payload.description

            if payload.is_active is not None:
                role.is_active = payload.is_active

            if payload.permissions is not None:
                permissions = set(payload.permissions)
                unknown = permissions - ALL_WORKSPACE_PERMISSIONS

                if unknown:
                    raise ValidationError(
                        "Unknown permissions: " + ", ".join(sorted(unknown))
                    )

                await self.repository.set_role_permissions(
                    role_id=role.id,
                    permissions=permissions,
                )

            permissions = await self.repository.get_role_permissions(role.id)
            await self.session.commit()

            return WorkspaceRolePublic(
                id=role.id,
                role_key=role.role_key,
                display_name=role.display_name,
                description=role.description,
                permissions=sorted(permissions),
                is_builtin=False,
                is_immutable=False,
                is_active=role.is_active,
            )

        except Exception:
            await self.session.rollback()
            raise

    async def delete_role(
        self,
        *,
        workspace_id: uuid.UUID,
        role_id: uuid.UUID,
        user: User,
    ) -> None:
        try:
            actor = await self._require(
                workspace_id=workspace_id,
                user=user,
                permission=WorkspacePermission.ROLES_MANAGE.value,
            )

            role = await self.repository.get_custom_role(
                workspace_id=workspace_id,
                role_id=role_id,
            )

            if role is None:
                raise ResourceNotFound(
                    "Custom workspace role was not found."
                )

            members = await self.repository.list_members(workspace_id)

            if any(member.role_key == role.role_key for member in members):
                raise ValidationError(
                    "Role is assigned to members and cannot be deleted."
                )

            permissions = await self.repository.get_role_permissions(role.id)
            await self._assert_grantable(actor, permissions)

            assigned_membership = await self.session.scalar(
                select(WorkspaceMembershipRoleAssignment.membership_id)
                .where(
                    WorkspaceMembershipRoleAssignment.custom_role_id
                    == role.id
                )
                .limit(1)
            )

            if assigned_membership is not None:
                raise ValidationError(
                    "Role has additional membership assignments "
                    "and cannot be deleted."
                )

            await self.repository.delete_custom_role(role)
            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise

    async def list_members(
        self,
        *,
        workspace_id: uuid.UUID,
        user: User,
    ) -> WorkspaceMemberListResponse:
        await self._require(
            workspace_id=workspace_id,
            user=user,
            permission=WorkspacePermission.MEMBERS_READ.value,
        )

        memberships = await self.repository.list_members(workspace_id)
        items: list[WorkspaceMemberPublic] = []

        for membership in memberships:
            moderation = await self.repository.get_moderation(membership.id)
            access = await self._member_access(membership)

            items.append(
                WorkspaceMemberPublic(
                    membership_id=membership.id,
                    user_id=membership.user_id,
                    email=membership.user.email,
                    username=membership.user.username,
                    role_key=membership.role_key,
                    status=membership.status,
                    moderation=self._moderation_public(moderation),
                    role_keys=list(access.role_keys),
                )
            )

        return WorkspaceMemberListResponse(
            workspace_id=workspace_id,
            members=items,
        )

    async def get_member_roles(
        self,
        *,
        workspace_id: uuid.UUID,
        membership_id: uuid.UUID,
        user: User,
    ):
        actor = await self._actor_membership(
            workspace_id=workspace_id,
            user=user,
        )
        access = await self._access(actor)

        if (
            actor.id != membership_id
            and WorkspacePermission.ROLES_READ.value not in access.permissions
            and WorkspacePermission.MEMBERS_READ.value
            not in access.permissions
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Workspace role read permission is required.",
            )

        target = await self._target(
            workspace_id=workspace_id,
            membership_id=membership_id,
        )

        return await self._member_roles_response(target)

    async def grant_member_role(
        self,
        *,
        workspace_id: uuid.UUID,
        membership_id: uuid.UUID,
        role_key: str,
        user: User,
    ):
        try:
            actor = await self._require(
                workspace_id=workspace_id,
                user=user,
                permission=WorkspacePermission.ROLES_ASSIGN.value,
            )
            normalized = self.assignment_repository.normalize_role_key(
                role_key
            )
            target = await self._target(
                workspace_id=workspace_id,
                membership_id=membership_id,
            )

            if target.status != MEMBERSHIP_STATUS_ACTIVE:
                raise ValidationError(
                    "Additional roles require an active membership."
                )

            if target.role_key == WORKSPACE_ROLE_OWNER:
                raise ValidationError(
                    "Owners do not need additional workspace roles."
                )

            moderation = await self.repository.get_moderation(target.id)

            if moderation is not None and moderation.is_banned:
                raise ValidationError(
                    "Additional roles cannot be granted "
                    "to a banned membership."
                )

            permissions = await self._assignment_permissions(
                workspace_id=workspace_id,
                role_key=normalized,
            )
            await self._assert_grantable(actor, permissions)

            await self.assignment_repository.add(
                workspace_id=workspace_id,
                membership_id=membership_id,
                role_key=normalized,
                granted_by_user_id=user.id,
            )

            response = await self._member_roles_response(target)
            await self.session.commit()

            return response

        except Exception:
            await self.session.rollback()
            raise

    async def revoke_member_role(
        self,
        *,
        workspace_id: uuid.UUID,
        membership_id: uuid.UUID,
        role_key: str,
        user: User,
    ):
        try:
            actor = await self._require(
                workspace_id=workspace_id,
                user=user,
                permission=WorkspacePermission.ROLES_ASSIGN.value,
            )
            normalized = self.assignment_repository.normalize_role_key(
                role_key
            )
            target = await self._target(
                workspace_id=workspace_id,
                membership_id=membership_id,
            )

            if target.role_key == WORKSPACE_ROLE_OWNER:
                raise ValidationError(
                    "Owner memberships cannot be changed "
                    "through role assignment actions."
                )

            if target.role_key.strip().lower() == normalized:
                raise ValidationError(
                    "Use the primary-role endpoint to change "
                    "the primary role."
                )

            permissions = await self._assignment_permissions(
                workspace_id=workspace_id,
                role_key=normalized,
                allow_inactive=True,
            )
            await self._assert_grantable(actor, permissions)

            await self.assignment_repository.remove(
                workspace_id=workspace_id,
                membership_id=membership_id,
                role_key=normalized,
            )

            response = await self._member_roles_response(target)
            await self.session.commit()

            return response

        except Exception:
            await self.session.rollback()
            raise

    async def update_member_role(
        self,
        payload: WorkspaceMemberRoleUpdateRequest,
        *,
        workspace_id: uuid.UUID,
        membership_id: uuid.UUID,
        user: User,
    ) -> WorkspaceMemberPublic:
        try:
            actor = await self._require(
                workspace_id=workspace_id,
                user=user,
                permission=WorkspacePermission.ROLES_ASSIGN.value,
            )

            membership = await self.repository.get_membership(
                workspace_id=workspace_id,
                membership_id=membership_id,
            )

            if membership is None:
                raise ResourceNotFound(
                    "Workspace membership was not found."
                )

            requested_role = payload.role_key.strip().lower()

            if requested_role not in BUILT_IN_ROLE_KEYS:
                custom = await self.repository.get_custom_role_by_key(
                    workspace_id=workspace_id,
                    role_key=requested_role,
                )

                if custom is None or not custom.is_active:
                    raise ValidationError(
                        "Workspace role does not exist."
                    )

            if requested_role == WORKSPACE_ROLE_OWNER:
                actor = await self._actor_membership(
                    workspace_id=workspace_id,
                    user=user,
                )

                if actor.role_key != WORKSPACE_ROLE_OWNER:
                    raise ValidationError(
                        "Only an owner can assign the owner role."
                    )

            if (
                membership.workspace_id != workspace_id
                or membership.status != MEMBERSHIP_STATUS_ACTIVE
            ):
                raise ResourceNotFound(
                    "Active workspace membership was not found."
                )

            if (
                membership.role_key == WORKSPACE_ROLE_OWNER
                and requested_role != WORKSPACE_ROLE_OWNER
            ):
                raise ValidationError(
                    "Owner demotion requires a dedicated "
                    "ownership transfer operation."
                )

            requested_permissions = await self._assignment_permissions(
                workspace_id=workspace_id,
                role_key=requested_role,
            )
            await self._assert_grantable(actor, requested_permissions)

            target_access = await self._member_access(membership)
            await self._assert_grantable(actor, target_access.permissions)

            if requested_role != WORKSPACE_ROLE_OWNER:
                await self.assignment_repository.remove(
                    workspace_id=workspace_id,
                    membership_id=membership_id,
                    role_key=requested_role,
                )

            membership.role_key = requested_role

            moderation = await self.repository.get_moderation(membership.id)
            access = await self._member_access(membership)

            response = WorkspaceMemberPublic(
                membership_id=membership.id,
                user_id=membership.user_id,
                email=membership.user.email,
                username=membership.user.username,
                role_key=membership.role_key,
                status=membership.status,
                moderation=self._moderation_public(moderation),
                role_keys=list(access.role_keys),
            )

            await self.session.commit()
            return response

        except Exception:
            await self.session.rollback()
            raise

    async def kick_member(
        self,
        *,
        workspace_id: uuid.UUID,
        membership_id: uuid.UUID,
        user: User,
    ) -> WorkspaceModerationActionResponse:
        try:
            await self._require(
                workspace_id=workspace_id,
                user=user,
                permission=WorkspacePermission.MEMBERS_KICK.value,
            )

            membership = await self._moderatable_member(
                workspace_id,
                membership_id,
            )
            membership.status = MEMBERSHIP_STATUS_REMOVED
            membership.removed_at = utc_now()

            await self.session.commit()

            moderation = await self.repository.get_moderation(membership.id)

            return WorkspaceModerationActionResponse(
                message="Member kicked.",
                membership_id=membership.id,
                moderation=self._moderation_public(moderation),
            )

        except Exception:
            await self.session.rollback()
            raise

    async def ban_member(
        self,
        *,
        workspace_id: uuid.UUID,
        membership_id: uuid.UUID,
        user: User,
    ) -> WorkspaceModerationActionResponse:
        try:
            await self._require(
                workspace_id=workspace_id,
                user=user,
                permission=WorkspacePermission.MEMBERS_BAN.value,
            )

            membership = await self._moderatable_member(
                workspace_id,
                membership_id,
            )
            moderation = await self.repository.get_or_create_moderation(
                membership.id
            )

            moderation.is_banned = True
            moderation.banned_at = utc_now()
            moderation.banned_by_user_id = user.id
            membership.status = MEMBERSHIP_STATUS_SUSPENDED
            membership.suspended_at = utc_now()

            await self.session.commit()

            return WorkspaceModerationActionResponse(
                message="Member banned.",
                membership_id=membership.id,
                moderation=self._moderation_public(moderation),
            )

        except Exception:
            await self.session.rollback()
            raise

    async def mute_member(
        self,
        *,
        workspace_id: uuid.UUID,
        membership_id: uuid.UUID,
        user: User,
    ) -> WorkspaceModerationActionResponse:
        try:
            await self._require(
                workspace_id=workspace_id,
                user=user,
                permission=WorkspacePermission.MEMBERS_MUTE.value,
            )

            membership = await self._moderatable_member(
                workspace_id,
                membership_id,
            )
            moderation = await self.repository.get_or_create_moderation(
                membership.id
            )
            moderation.is_muted = not moderation.is_muted

            await self.session.commit()

            return WorkspaceModerationActionResponse(
                message="Member mute state updated.",
                membership_id=membership.id,
                moderation=self._moderation_public(moderation),
            )

        except Exception:
            await self.session.rollback()
            raise

    async def deafen_member(
        self,
        *,
        workspace_id: uuid.UUID,
        membership_id: uuid.UUID,
        user: User,
    ) -> WorkspaceModerationActionResponse:
        try:
            await self._require(
                workspace_id=workspace_id,
                user=user,
                permission=WorkspacePermission.MEMBERS_DEAFEN.value,
            )

            membership = await self._moderatable_member(
                workspace_id,
                membership_id,
            )
            moderation = await self.repository.get_or_create_moderation(
                membership.id
            )
            moderation.is_deafened = not moderation.is_deafened

            await self.session.commit()

            return WorkspaceModerationActionResponse(
                message="Member deafen state updated.",
                membership_id=membership.id,
                moderation=self._moderation_public(moderation),
            )

        except Exception:
            await self.session.rollback()
            raise

    async def update_visibility(
        self,
        payload: WorkspaceMemberVisibilityRequest,
        *,
        workspace_id: uuid.UUID,
        membership_id: uuid.UUID,
        user: User,
    ) -> WorkspaceModerationActionResponse:
        try:
            await self._require(
                workspace_id=workspace_id,
                user=user,
                permission=WorkspacePermission.MEMBERS_HIDE.value,
            )

            membership = await self._moderatable_member(
                workspace_id,
                membership_id,
            )
            moderation = await self.repository.get_or_create_moderation(
                membership.id
            )
            moderation.is_hidden = payload.hidden

            await self.session.commit()

            return WorkspaceModerationActionResponse(
                message="Member visibility updated.",
                membership_id=membership.id,
                moderation=self._moderation_public(moderation),
            )

        except Exception:
            await self.session.rollback()
            raise

    async def bootstrap(
        self,
        *,
        workspace_id: uuid.UUID,
        user: User,
    ) -> WorkspaceBootstrapResponse:
        membership = await self._actor_membership(
            workspace_id=workspace_id,
            user=user,
        )
        access = await self._access(membership)
        moderation = await self.repository.get_moderation(membership.id)
        roles = await self.list_roles(workspace_id=workspace_id, user=user)

        return WorkspaceBootstrapResponse(
            workspace_id=workspace_id,
            membership_id=membership.id,
            role_key=membership.role_key,
            role_keys=list(access.role_keys),
            permissions=sorted(access.permissions),
            moderation=self._moderation_public(moderation),
            available_roles=roles.roles,
        )

    async def _moderatable_member(
        self,
        workspace_id: uuid.UUID,
        membership_id: uuid.UUID,
    ):
        membership = await self.repository.get_membership(
            workspace_id=workspace_id,
            membership_id=membership_id,
        )

        if membership is None:
            raise ResourceNotFound("Workspace membership was not found.")

        if membership.role_key == WORKSPACE_ROLE_OWNER:
            raise ValidationError(
                "Workspace owner cannot be moderated "
                "through member actions."
            )

        return membership

    def _moderation_public(
        self,
        moderation,
    ) -> WorkspaceMemberModerationPublic:
        if moderation is None:
            return WorkspaceMemberModerationPublic()

        return WorkspaceMemberModerationPublic(
            is_banned=moderation.is_banned,
            is_muted=moderation.is_muted,
            is_deafened=moderation.is_deafened,
            is_hidden=moderation.is_hidden,
        )


__all__ = ["WorkspaceRBACService"]