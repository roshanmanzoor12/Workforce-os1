from __future__ import annotations

import re
import secrets
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ConflictError,
    ResourceNotFound,
    ValidationError,
)
from app.modules.auth.models import User
from app.modules.billing.exceptions import (
    WorkspaceEntitlementDeniedError,
)
from app.modules.billing.workspace_access import (
    WorkspaceEntitlementAccess,
)
from app.modules.workspaces.models import (
    MEMBERSHIP_STATUS_ACTIVE,
    MEMBERSHIP_STATUS_REMOVED,
    MEMBERSHIP_STATUS_SUSPENDED,
    TENANT_STATUS_DECOMMISSIONED,
    TENANT_STATUS_PENDING,
    TENANT_STATUS_SUSPENDED,
    WORKSPACE_ROLE_ADMIN,
    WORKSPACE_ROLE_MEMBER,
    WORKSPACE_ROLE_OWNER,
    WORKSPACE_STATUS_ARCHIVED,
    WORKSPACE_STATUS_PROVISIONING,
    WORKSPACE_STATUS_SUSPENDED,
    TenantDatabaseRegistry,
    Workspace,
    WorkspaceMembership,
)
from app.modules.workspaces.provisioning import (
    WorkspaceProvisioningResult,
    provision_workspace_tenant,
    retry_workspace_tenant_provisioning,
)
from app.modules.workspaces.repository import WorkspaceRepository
from app.modules.workspaces.schemas import (
    TenantDatabasePublic,
    UserWorkspacePublic,
    WorkspaceCreateRequest,
    WorkspaceCreateResponse,
    WorkspaceDetailResponse,
    WorkspaceListResponse,
    WorkspaceMembershipPublic,
    WorkspaceMembershipRemoveResponse,
    WorkspaceMembershipResponse,
    WorkspaceMembershipRoleUpdateRequest,
    WorkspaceMembershipStatusUpdateRequest,
    WorkspacePublic,
    WorkspaceStateResponse,
    WorkspaceUpdateRequest,
)


# =========================================================
# TIME
# =========================================================


def utc_now() -> datetime:
    return datetime.now(
        timezone.utc
    )


# =========================================================
# WORKSPACE SERVICE
# =========================================================


class WorkspaceService:
    """
    WorkforceOS control-plane workspace service.

    Responsibilities:

    - create global workspaces
    - create owner memberships
    - register server-owned tenant database identities
    - provision registered tenant databases
    - retry failed tenant provisioning
    - list current user's workspaces
    - resolve authorized workspace context
    - update workspace metadata
    - manage basic membership roles/status
    - suspend/archive workspaces

    Security rules:

    - clients never choose database names
    - clients never provide database URLs
    - tenant database identity is derived server-side
    - tenant provisioning requires workspace authorization
    - physical tenant routing occurs only after membership checks
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

        self.repository = WorkspaceRepository(
            session
        )

    # =====================================================
    # CREATE WORKSPACE
    # =====================================================

    async def create_workspace(
        self,
        request: WorkspaceCreateRequest,
        *,
        user: User,
    ) -> WorkspaceCreateResponse:
        """
        Create durable workspace control-plane records.

        Transaction:

            generate unique slug
                â†“
            create workspace
                â†“
            create owner membership
                â†“
            generate server-owned tenant database name
                â†“
            create tenant registry record
                â†“
            commit

        The workspace is intentionally committed before physical
        PostgreSQL provisioning begins.

        This gives provisioning a durable control-plane identity and
        allows safe retries if CREATE DATABASE, migration, or tenant
        initialization fails.
        """

        entitlement_access = WorkspaceEntitlementAccess(
            self.session
        )

        slug = await self._allocate_workspace_slug(
            requested_slug=request.slug,
            workspace_name=request.name,
        )

        entitlement_access = WorkspaceEntitlementAccess(
            self.session
        )

        try:
            await entitlement_access.require_workspace_creation(
                user_id=user.id
            )

        except WorkspaceEntitlementDeniedError as exc:
            raise ValidationError(
                str(exc)
            ) from exc

        now = utc_now()

        try:
            workspace = await self.repository.create_workspace(
                name=request.name,
                slug=slug,
                created_by_user_id=user.id,
                timezone=request.timezone,
                workspace_type=request.workspace_type,
                logo_url=request.logo_url,
                status=WORKSPACE_STATUS_PROVISIONING,
                is_active=True,
            )

            membership = await self.repository.create_membership(
                workspace_id=workspace.id,
                user_id=user.id,
                role_key=WORKSPACE_ROLE_OWNER,
                status=MEMBERSHIP_STATUS_ACTIVE,
                joined_at=now,
            )

            database_name = (
                self._build_tenant_database_name(
                    workspace.id
                )
            )

            if (
                await self.repository.tenant_database_name_exists(
                    database_name
                )
            ):
                raise ConflictError(
                    "Unable to allocate tenant database identity."
                )

            tenant = (
                await self.repository.create_tenant_database_registry(
                    workspace_id=workspace.id,
                    database_name=database_name,
                    cluster_key="primary",
                    status=TENANT_STATUS_PENDING,
                    schema_version=None,
                )
            )

            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise

        return WorkspaceCreateResponse(
            message=(
                "Workspace created. "
                "Tenant database provisioning is pending."
            ),
            workspace=self._workspace_public(
                workspace
            ),
            membership=self._membership_public(
                membership
            ),
            tenant=self._tenant_public(
                tenant
            ),
        )

    # =====================================================
    # PROVISION TENANT
    # =====================================================

    async def provision_workspace(
        self,
        *,
        workspace_id: uuid.UUID,
        user: User,
    ) -> WorkspaceProvisioningResult:
        """
        Provision the physical tenant database for a workspace.

        Only an active workspace owner may start provisioning.

        Security flow:

            authenticated global user
                â†“
            authorized workspace membership
                â†“
            owner role required
                â†“
            trusted TenantDatabaseRegistry
                â†“
            CREATE DATABASE
                â†“
            tenant Alembic migration
                â†“
            tenant metadata initialization
                â†“
            workspace + tenant become ready

        database_name is never accepted as an argument.
        """

        _, membership, _ = (
            await self._require_workspace_context(
                workspace_id=workspace_id,
                user_id=user.id,
            )
        )

        self._require_owner(
            membership
        )

        return await provision_workspace_tenant(
            self.session,
            workspace_id=workspace_id,
        )

    # =====================================================
    # RETRY TENANT PROVISIONING
    # =====================================================

    async def retry_workspace_provisioning(
        self,
        *,
        workspace_id: uuid.UUID,
        user: User,
    ) -> WorkspaceProvisioningResult:
        """
        Retry tenant provisioning using the existing trusted registry.

        A retry does not generate a different database name.

        Only an active workspace owner may retry provisioning.
        """

        _, membership, _ = (
            await self._require_workspace_context(
                workspace_id=workspace_id,
                user_id=user.id,
            )
        )

        self._require_owner(
            membership
        )

        return await retry_workspace_tenant_provisioning(
            self.session,
            workspace_id=workspace_id,
        )

    # =====================================================
    # LIST CURRENT USER WORKSPACES
    # =====================================================

    async def list_user_workspaces(
        self,
        *,
        user: User,
    ) -> WorkspaceListResponse:
        memberships = (
            await self.repository.list_user_memberships(
                user.id,
                include_inactive=False,
            )
        )

        items: list[UserWorkspacePublic] = []

        for membership in memberships:
            workspace = membership.workspace

            if not workspace.is_active:
                continue

            tenant = workspace.tenant_database

            items.append(
                UserWorkspacePublic(
                    workspace=self._workspace_public(
                        workspace
                    ),
                    membership=self._membership_public(
                        membership
                    ),
                    tenant=(
                        self._tenant_public(
                            tenant
                        )
                        if tenant is not None
                        else None
                    ),
                )
            )

        return WorkspaceListResponse(
            workspaces=items,
            total=len(items),
        )

    # =====================================================
    # WORKSPACE DETAIL
    # =====================================================

    async def get_workspace(
        self,
        *,
        workspace_id: uuid.UUID,
        user: User,
    ) -> WorkspaceDetailResponse:
        context = (
            await self.repository.get_authorized_workspace(
                workspace_id=workspace_id,
                user_id=user.id,
            )
        )

        if context is None:
            raise ResourceNotFound(
                "Workspace was not found."
            )

        workspace, membership, tenant = context

        return WorkspaceDetailResponse(
            workspace=self._workspace_public(
                workspace
            ),
            membership=self._membership_public(
                membership
            ),
            tenant=(
                self._tenant_public(
                    tenant
                )
                if tenant is not None
                else None
            ),
        )

    # =====================================================
    # UPDATE WORKSPACE
    # =====================================================

    async def update_workspace(
        self,
        request: WorkspaceUpdateRequest,
        *,
        workspace_id: uuid.UUID,
        user: User,
    ) -> WorkspaceDetailResponse:
        workspace, membership, tenant = (
            await self._require_workspace_context(
                workspace_id=workspace_id,
                user_id=user.id,
            )
        )

        self._require_admin_or_owner(
            membership
        )

        if (
            workspace.status
            == WORKSPACE_STATUS_ARCHIVED
        ):
            raise ValidationError(
                "Archived workspaces cannot be modified."
            )

        try:
            workspace = (
                await self.repository.update_workspace(
                    workspace,
                    name=request.name,
                    timezone=request.timezone,
                    workspace_type=request.workspace_type,
                    logo_url=request.logo_url,
                )
            )

            if request.primary_color is not None:
                workspace.primary_color = request.primary_color
            if request.accent_color is not None:
                workspace.accent_color = request.accent_color
            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise

        return WorkspaceDetailResponse(
            workspace=self._workspace_public(
                workspace
            ),
            membership=self._membership_public(
                membership
            ),
            tenant=(
                self._tenant_public(
                    tenant
                )
                if tenant is not None
                else None
            ),
        )

    # =====================================================
    # MEMBERSHIP ROLE
    # =====================================================

    async def update_membership_role(
        self,
        request: WorkspaceMembershipRoleUpdateRequest,
        *,
        workspace_id: uuid.UUID,
        membership_id: uuid.UUID,
        user: User,
    ) -> WorkspaceMembershipResponse:
        _, actor_membership, _ = (
            await self._require_workspace_context(
                workspace_id=workspace_id,
                user_id=user.id,
            )
        )

        self._require_owner(
            actor_membership
        )

        target = (
            await self.repository.get_membership_by_id(
                membership_id
            )
        )

        if (
            target is None
            or target.workspace_id
            != workspace_id
        ):
            raise ResourceNotFound(
                "Workspace membership was not found."
            )

        if (
            target.status
            == MEMBERSHIP_STATUS_REMOVED
        ):
            raise ValidationError(
                "Removed memberships cannot change role."
            )

        if (
            target.role_key
            == WORKSPACE_ROLE_OWNER
            and request.role_key
            != WORKSPACE_ROLE_OWNER
        ):
            owner_count = (
                await self.repository.count_workspace_owners(
                    workspace_id,
                    active_only=True,
                )
            )

            if (
                owner_count <= 1
                and target.status
                == MEMBERSHIP_STATUS_ACTIVE
            ):
                raise ValidationError(
                    "A workspace must have at least one active owner."
                )

        try:
            target = (
                await self.repository.update_membership_role(
                    target,
                    role_key=request.role_key,
                )
            )

            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise

        return WorkspaceMembershipResponse(
            message=(
                "Workspace membership role updated."
            ),
            membership=self._membership_public(
                target
            ),
        )

    # =====================================================
    # MEMBERSHIP STATUS
    # =====================================================

    async def update_membership_status(
        self,
        request: WorkspaceMembershipStatusUpdateRequest,
        *,
        workspace_id: uuid.UUID,
        membership_id: uuid.UUID,
        user: User,
    ) -> WorkspaceMembershipResponse:
        _, actor_membership, _ = (
            await self._require_workspace_context(
                workspace_id=workspace_id,
                user_id=user.id,
            )
        )

        self._require_admin_or_owner(
            actor_membership
        )

        target = (
            await self.repository.get_membership_by_id(
                membership_id
            )
        )

        if (
            target is None
            or target.workspace_id
            != workspace_id
        ):
            raise ResourceNotFound(
                "Workspace membership was not found."
            )

        if (
            actor_membership.role_key
            == WORKSPACE_ROLE_ADMIN
            and target.role_key
            == WORKSPACE_ROLE_OWNER
        ):
            raise ValidationError(
                "Workspace admins cannot modify owner memberships."
            )

        if (
            target.role_key
            == WORKSPACE_ROLE_OWNER
            and request.status
            != MEMBERSHIP_STATUS_ACTIVE
            and target.status
            == MEMBERSHIP_STATUS_ACTIVE
        ):
            owner_count = (
                await self.repository.count_workspace_owners(
                    workspace_id,
                    active_only=True,
                )
            )

            if owner_count <= 1:
                raise ValidationError(
                    "A workspace must have at least one active owner."
                )

        now = utc_now()

        joined_at = None
        suspended_at = None
        removed_at = None

        if (
            request.status
            == MEMBERSHIP_STATUS_ACTIVE
        ):
            if target.joined_at is None:
                joined_at = now

        elif (
            request.status
            == MEMBERSHIP_STATUS_SUSPENDED
        ):
            suspended_at = now

        elif (
            request.status
            == MEMBERSHIP_STATUS_REMOVED
        ):
            removed_at = now

        try:
            target = (
                await self.repository.update_membership_status(
                    target,
                    status=request.status,
                    joined_at=joined_at,
                    suspended_at=suspended_at,
                    removed_at=removed_at,
                )
            )

            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise

        return WorkspaceMembershipResponse(
            message=(
                "Workspace membership status updated."
            ),
            membership=self._membership_public(
                target
            ),
        )

    # =====================================================
    # REMOVE MEMBERSHIP
    # =====================================================

    async def remove_membership(
        self,
        *,
        workspace_id: uuid.UUID,
        membership_id: uuid.UUID,
        user: User,
    ) -> WorkspaceMembershipRemoveResponse:
        _, actor_membership, _ = (
            await self._require_workspace_context(
                workspace_id=workspace_id,
                user_id=user.id,
            )
        )

        self._require_admin_or_owner(
            actor_membership
        )

        target = (
            await self.repository.get_membership_by_id(
                membership_id
            )
        )

        if (
            target is None
            or target.workspace_id
            != workspace_id
        ):
            raise ResourceNotFound(
                "Workspace membership was not found."
            )

        if (
            actor_membership.role_key
            == WORKSPACE_ROLE_ADMIN
            and target.role_key
            == WORKSPACE_ROLE_OWNER
        ):
            raise ValidationError(
                "Workspace admins cannot remove owners."
            )

        if (
            target.status
            == MEMBERSHIP_STATUS_REMOVED
        ):
            return (
                WorkspaceMembershipRemoveResponse(
                    message=(
                        "Workspace membership already removed."
                    ),
                    success=True,
                )
            )

        if (
            target.role_key
            == WORKSPACE_ROLE_OWNER
            and target.status
            == MEMBERSHIP_STATUS_ACTIVE
        ):
            owner_count = (
                await self.repository.count_workspace_owners(
                    workspace_id,
                    active_only=True,
                )
            )

            if owner_count <= 1:
                raise ValidationError(
                    "The last active workspace owner cannot be removed."
                )

        try:
            await self.repository.update_membership_status(
                target,
                status=MEMBERSHIP_STATUS_REMOVED,
                removed_at=utc_now(),
            )

            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise

        return WorkspaceMembershipRemoveResponse(
            message="Workspace membership removed.",
            success=True,
        )

    # =====================================================
    # SUSPEND WORKSPACE
    # =====================================================

    async def suspend_workspace(
        self,
        *,
        workspace_id: uuid.UUID,
        user: User,
    ) -> WorkspaceStateResponse:
        workspace, membership, tenant = (
            await self._require_workspace_context(
                workspace_id=workspace_id,
                user_id=user.id,
            )
        )

        self._require_owner(
            membership
        )

        if (
            workspace.status
            == WORKSPACE_STATUS_ARCHIVED
        ):
            raise ValidationError(
                "Archived workspaces cannot be suspended."
            )

        try:
            await self.repository.set_workspace_status(
                workspace,
                status=WORKSPACE_STATUS_SUSPENDED,
            )

            if tenant is not None:
                await self.repository.set_tenant_database_status(
                    tenant,
                    status=TENANT_STATUS_SUSPENDED,
                )

            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise

        return WorkspaceStateResponse(
            message="Workspace suspended.",
            workspace=self._workspace_public(
                workspace
            ),
        )

    # =====================================================
    # ARCHIVE WORKSPACE
    # =====================================================

    async def archive_workspace(
        self,
        *,
        workspace_id: uuid.UUID,
        user: User,
    ) -> WorkspaceStateResponse:
        workspace, membership, tenant = (
            await self._require_workspace_context(
                workspace_id=workspace_id,
                user_id=user.id,
            )
        )

        self._require_owner(
            membership
        )

        if (
            workspace.status
            == WORKSPACE_STATUS_ARCHIVED
        ):
            return WorkspaceStateResponse(
                message=(
                    "Workspace is already archived."
                ),
                workspace=self._workspace_public(
                    workspace
                ),
            )

        try:
            await self.repository.set_workspace_status(
                workspace,
                status=WORKSPACE_STATUS_ARCHIVED,
            )

            await self.repository.set_workspace_active(
                workspace,
                active=False,
            )

            if tenant is not None:
                await self.repository.set_tenant_database_status(
                    tenant,
                    status=TENANT_STATUS_DECOMMISSIONED,
                )

            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise

        return WorkspaceStateResponse(
            message="Workspace archived.",
            workspace=self._workspace_public(
                workspace
            ),
        )

    # =====================================================
    # AUTHORIZED CONTEXT
    # =====================================================

    async def get_authorized_workspace_context(
        self,
        *,
        workspace_id: uuid.UUID,
        user: User,
    ) -> tuple[
        Workspace,
        WorkspaceMembership,
        TenantDatabaseRegistry | None,
    ]:
        """
        Resolve trusted control-plane workspace context.

        The client supplies only workspace_id.

        database_name is resolved internally from
        workforce_control after membership authorization.
        """

        return await self._require_workspace_context(
            workspace_id=workspace_id,
            user_id=user.id,
        )

    # =====================================================
    # INTERNAL CONTEXT LOOKUP
    # =====================================================

    async def _require_workspace_context(
        self,
        *,
        workspace_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> tuple[
        Workspace,
        WorkspaceMembership,
        TenantDatabaseRegistry | None,
    ]:
        context = (
            await self.repository.get_authorized_workspace(
                workspace_id=workspace_id,
                user_id=user_id,
            )
        )

        if context is None:
            raise ResourceNotFound(
                "Workspace was not found."
            )

        return context

    # =====================================================
    # ROLE POLICY
    # =====================================================

    def _require_owner(
        self,
        membership: WorkspaceMembership,
    ) -> None:
        if (
            membership.role_key
            != WORKSPACE_ROLE_OWNER
        ):
            raise ValidationError(
                "Workspace owner permission is required."
            )

    def _require_admin_or_owner(
        self,
        membership: WorkspaceMembership,
    ) -> None:
        if membership.role_key not in {
            WORKSPACE_ROLE_OWNER,
            WORKSPACE_ROLE_ADMIN,
        }:
            raise ValidationError(
                "Workspace administrator permission is required."
            )

    # =====================================================
    # SLUG ALLOCATION
    # =====================================================
    async def _allocate_workspace_slug(
        self,
        *,
        requested_slug: str | None,
        workspace_name: str,
    ) -> str:
        if requested_slug is not None:
            base = (
                requested_slug
                .strip()
                .lower()
            )

            if not base:
                raise ConflictError(
                    "Workspace slug cannot be empty."
                )

            if await self.repository.workspace_slug_exists(
                base
            ):
                raise ConflictError(
                    "Workspace slug is already in use."
                )

            return base

        base = self._slugify(
            workspace_name
        )

        if not base:
            raise ConflictError(
                "Unable to generate a workspace slug."
            )

        if not await self.repository.workspace_slug_exists(
            base
        ):
            return base

        for _ in range(20):
            suffix = secrets.token_hex(
                3
            )

            candidate = (
                f"{base[:93]}-{suffix}"
            )

            if not await self.repository.workspace_slug_exists(
                candidate
            ):
                return candidate

        raise ConflictError(
            "Unable to allocate a unique workspace slug."
        )

    def _slugify(
        self,
        value: str,
    ) -> str:
        normalized = (
            value
            .strip()
            .lower()
        )

        normalized = re.sub(
            r"[^a-z0-9]+",
            "-",
            normalized,
        )

        normalized = normalized.strip(
            "-"
        )

        normalized = re.sub(
            r"-+",
            "-",
            normalized,
        )

        if len(normalized) < 2:
            normalized = "workspace"

        return normalized[:100]

    # =====================================================
    # TENANT DATABASE IDENTITY
    # =====================================================

    def _build_tenant_database_name(
        self,
        workspace_id: uuid.UUID,
    ) -> str:
        """
        Generate server-owned PostgreSQL tenant database name.

        Client input is never used.

        Example:

            tenant_123e4567e89b12d3a456426614174000
        """

        return (
            f"tenant_{workspace_id.hex}"
        )

    # =====================================================
    # SAFE OUTPUT MAPPERS
    # =====================================================

    def _workspace_public(
        self,
        workspace: Workspace,
    ) -> WorkspacePublic:
        return WorkspacePublic.model_validate(
            workspace
        )

    def _membership_public(
        self,
        membership: WorkspaceMembership,
    ) -> WorkspaceMembershipPublic:
        return WorkspaceMembershipPublic.model_validate(
            membership
        )

    def _tenant_public(
        self,
        tenant: TenantDatabaseRegistry,
    ) -> TenantDatabasePublic:
        return TenantDatabasePublic.model_validate(
            tenant
        )


# =========================================================
# FACTORY
# =========================================================


def get_workspace_service(
    session: AsyncSession,
) -> WorkspaceService:
    return WorkspaceService(
        session
    )


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "WorkspaceService",
    "get_workspace_service",
]
