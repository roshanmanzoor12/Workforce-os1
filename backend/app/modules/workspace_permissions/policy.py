from __future__ import annotations

from app.modules.workspace_permissions.permissions import (
    ALL_WORKSPACE_PERMISSIONS,
)
from app.modules.workspace_permissions.roles import (
    OWNER_ROLE,
    ROLE_PERMISSIONS,
)


class WorkspacePermissionPolicy:
    @staticmethod
    def normalize_role_key(
        role_key: str | None,
    ) -> str | None:
        if role_key is None:
            return None

        return (
            role_key
            .strip()
            .lower()
        )

    @classmethod
    def permissions_for_role(
        cls,
        role_key: str | None,
    ) -> frozenset[str]:
        normalized = (
            cls.normalize_role_key(
                role_key
            )
        )

        if normalized is None:
            return frozenset()

        if normalized == OWNER_ROLE:
            return (
                ALL_WORKSPACE_PERMISSIONS
            )

        return ROLE_PERMISSIONS.get(
            normalized,
            frozenset(),
        )

    @classmethod
    def allows(
        cls,
        *,
        role_key: str | None,
        permission: str,
    ) -> bool:
        return (
            permission
            in cls.permissions_for_role(
                role_key
            )
        )

    @classmethod
    def allows_all(
        cls,
        *,
        role_key: str | None,
        permissions: set[str]
        | frozenset[str],
    ) -> bool:
        role_permissions = (
            cls.permissions_for_role(
                role_key
            )
        )

        return permissions.issubset(
            role_permissions
        )

    @classmethod
    def allows_any(
        cls,
        *,
        role_key: str | None,
        permissions: set[str]
        | frozenset[str],
    ) -> bool:
        role_permissions = (
            cls.permissions_for_role(
                role_key
            )
        )

        return bool(
            role_permissions
            .intersection(
                permissions
            )
        )

    @classmethod
    def require_permission(
        cls,
        *,
        role_key: str | None,
        permission: str,
    ) -> None:
        if cls.allows(
            role_key=role_key,
            permission=permission,
        ):
            return

        raise PermissionError(
            f"Workspace permission required: "
            f"{permission}"
        )


__all__ = [
    "WorkspacePermissionPolicy",
]