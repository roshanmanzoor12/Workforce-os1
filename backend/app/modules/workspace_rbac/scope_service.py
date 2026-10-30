from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.workspace_permissions.effective import (
    resolve_membership_permissions,
)
from app.modules.workspace_rbac.scope_policy import (
    require_scope_manager,
)
from app.modules.workspace_rbac.scope_repository import (
    MembershipScopeGrantRepository,
)
from app.modules.workspace_rbac.scope_resources import (
    TenantScopeResourceValidator,
)
from app.modules.workspace_rbac.scope_schemas import (
    ScopeGrantCreateRequest,
    ScopeGrantDeleteResponse,
    ScopeGrantListResponse,
    ScopeGrantPublic,
)


class MembershipScopeGrantService:
    """
    Application service for saved scope administration.

    Receives an authorized tenant scope from server-side dependencies.
    Actor identity is taken from that scope, never from request payloads.

    The control session is committed only after all validation succeeds.
    The tenant session is used only for resource validation.
    """

    def __init__(
        self,
        control_session: AsyncSession,
        tenant_scope: object,
    ) -> None:
        self.session = control_session
        self.scope = tenant_scope

        for name in ("workspace_id", "user_id", "membership_id"):
            if not isinstance(
                getattr(tenant_scope, name, None),
                uuid.UUID,
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Authorized scope-management identity is unavailable.",
                )

        self.workspace_id = tenant_scope.workspace_id
        self.actor_user_id = tenant_scope.user_id
        self.actor_membership_id = tenant_scope.membership_id

        self.repository = MembershipScopeGrantRepository(
            control_session,
        )

        self.resources = TenantScopeResourceValidator(
            workspace_id=self.workspace_id,
            tenant_scope=tenant_scope,
        )

    async def _authorize(self, *, lock: bool):
        await self.repository.require_workspace(
            workspace_id=self.workspace_id,
            lock=lock,
        )

        actor = await self.repository.require_membership(
            workspace_id=self.workspace_id,
            membership_id=self.actor_membership_id,
            active_only=True,
            lock=lock,
        )

        permissions = await resolve_membership_permissions(
            self.session,
            workspace_id=self.workspace_id,
            membership=actor,
        )

        require_scope_manager(
            actor,
            workspace_id=self.workspace_id,
            actor_user_id=self.actor_user_id,
            permissions=permissions,
        )

        return actor

    async def list_for(
        self,
        *,
        membership_id: uuid.UUID,
    ) -> ScopeGrantListResponse:
        await self._authorize(lock=False)

        await self.repository.require_membership(
            workspace_id=self.workspace_id,
            membership_id=membership_id,
            active_only=True,
        )

        grants = await self.repository.list_for(
            workspace_id=self.workspace_id,
            membership_id=membership_id,
        )

        return ScopeGrantListResponse(
            membership_id=membership_id,
            grants=[
                ScopeGrantPublic.model_validate(grant)
                for grant in grants
            ],
        )

    async def grant(
        self,
        payload: ScopeGrantCreateRequest,
        *,
        membership_id: uuid.UUID,
    ) -> ScopeGrantPublic:
        try:
            actor = await self._authorize(lock=True)

            target = await self.repository.require_membership(
                workspace_id=self.workspace_id,
                membership_id=membership_id,
                active_only=True,
                lock=True,
            )

            # Includes the existing banned-membership check.
            await resolve_membership_permissions(
                self.session,
                workspace_id=self.workspace_id,
                membership=target,
            )

            await self.resources.require_active(
                scope_type=payload.scope_type,
                resource_id=payload.resource_id,
            )

            grant = await self.repository.add(
                workspace_id=self.workspace_id,
                membership_id=membership_id,
                scope_type=payload.scope_type,
                resource_id=payload.resource_id,
                granted_by_user_id=actor.user_id,
            )

            response = ScopeGrantPublic.model_validate(grant)

            await self.session.commit()
            return response

        except Exception:
            await self.session.rollback()
            raise

    async def revoke(
        self,
        *,
        membership_id: uuid.UUID,
        scope_type: str,
        resource_id: uuid.UUID,
    ) -> ScopeGrantDeleteResponse:
        try:
            await self._authorize(lock=True)

            removed = await self.repository.remove(
                workspace_id=self.workspace_id,
                membership_id=membership_id,
                scope_type=scope_type,
                resource_id=resource_id,
            )

            response = ScopeGrantDeleteResponse(
                membership_id=membership_id,
                scope_type=scope_type,
                resource_id=resource_id,
                removed=removed,
            )

            await self.session.commit()
            return response

        except Exception:
            await self.session.rollback()
            raise


__all__ = ["MembershipScopeGrantService"]