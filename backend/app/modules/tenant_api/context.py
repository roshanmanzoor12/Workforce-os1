from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(slots=True)
class AuthorizedTenantContext:
    """
    Request-scoped tenant context.

    control_session:
        workforce_control database.

    tenant_session:
        already-authorized workspace tenant database.

    Browser/frontend must never provide a database URL/name.
    """

    workspace_id: uuid.UUID
    actor_user_id: uuid.UUID

    control_session: AsyncSession
    tenant_session: AsyncSession


__all__ = [
    "AuthorizedTenantContext",
]