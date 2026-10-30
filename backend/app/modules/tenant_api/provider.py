from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable

from sqlalchemy.ext.asyncio import AsyncSession


TenantSessionResolver = Callable[
    [
        uuid.UUID,
        uuid.UUID,
        AsyncSession,
    ],
    Awaitable[AsyncSession],
]


_tenant_session_resolver: (
    TenantSessionResolver | None
) = None


def register_tenant_session_resolver(
    resolver: TenantSessionResolver,
) -> None:
    """
    Register the project's real authorized tenant-session resolver.

    Arguments passed to resolver:

        workspace_id
        actor_user_id
        control_session

    The browser never supplies database names, URLs, credentials,
    or tenant connection strings.
    """

    global _tenant_session_resolver

    _tenant_session_resolver = resolver


def get_registered_tenant_session_resolver(
) -> TenantSessionResolver:
    if _tenant_session_resolver is None:
        raise RuntimeError(
            "Tenant session resolver has not "
            "been registered."
        )

    return _tenant_session_resolver


def tenant_session_resolver_registered(
) -> bool:
    return (
        _tenant_session_resolver
        is not None
    )


__all__ = [
    "TenantSessionResolver",
    "register_tenant_session_resolver",
    "get_registered_tenant_session_resolver",
    "tenant_session_resolver_registered",
]