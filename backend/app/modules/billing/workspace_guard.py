from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from .account_service import (
    AccountBillingService,
    WorkspaceCountLoader,
)
from .entitlements import AccountEntitlements
from .exceptions import (
    WorkspaceEntitlementDeniedError,
)


class WorkspaceCreationGuard:
    def __init__(
        self,
        *,
        billing_service: AccountBillingService | None = None,
    ) -> None:
        self._billing_service = (
            billing_service
            or AccountBillingService()
        )

    async def require_allowed(
        self,
        session: AsyncSession,
        *,
        user_id: uuid.UUID,
        workspace_count_loader: WorkspaceCountLoader,
    ) -> AccountEntitlements:
        from sqlalchemy import select
        from app.modules.auth.models import User

        await session.execute(
            select(User.id).where(User.id == user_id).with_for_update()
        )

        entitlements = (
            await self._billing_service
            .get_entitlements(
                session,
                user_id=user_id,
                workspace_count_loader=workspace_count_loader,
            )
        )

        if not entitlements.create_workspace:
            raise WorkspaceEntitlementDeniedError(
                self._build_denial_reason(
                    entitlements
                )
            )

        return entitlements

    @staticmethod
    def _build_denial_reason(
        entitlements: AccountEntitlements,
    ) -> str:
        if (
            entitlements.workspace_limit is not None
            and entitlements.workspace_limit <= 0
        ):
            return (
                "Current plan does not include "
                "workspace creation."
            )

        if (
            entitlements.workspace_limit is not None
            and entitlements.workspace_count >= entitlements.workspace_limit
        ):
            return (
                "Workspace limit reached for "
                "the current plan."
            )

        return (
            "Current subscription state does not "
            "permit workspace creation."
        )
