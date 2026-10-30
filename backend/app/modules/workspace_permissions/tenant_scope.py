from __future__ import annotations

from app.db.tenant_dependency import (
    TenantScope,
)


def get_scope_role(
    scope: TenantScope,
) -> str | None:
    """
    Resolve role only from trusted backend TenantScope.

    Client request bodies/query parameters never supply the role.
    """

    role_key = getattr(
        scope,
        "role_key",
        None,
    )

    if isinstance(
        role_key,
        str,
    ):
        return (
            role_key
            .strip()
            .lower()
        )

    context = getattr(
        scope,
        "context",
        None,
    )

    if context is None:
        return None

    role_key = getattr(
        context,
        "role_key",
        None,
    )

    if isinstance(
        role_key,
        str,
    ):
        return (
            role_key
            .strip()
            .lower()
        )

    return None


__all__ = [
    "get_scope_role",
]