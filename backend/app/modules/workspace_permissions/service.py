from __future__ import annotations

from collections.abc import Iterable

from fastapi import HTTPException, status

from app.modules.workspace_permissions.permissions import (
    ALL_WORKSPACE_PERMISSIONS,
)
from app.modules.workspace_permissions.policy import (
    WorkspacePermissionPolicy,
)


class WorkspacePermissionService:
    def __init__(self, scope: object) -> None:
        self.scope = scope

    @property
    def role_key(self) -> str:
        value = getattr(self.scope, "role_key", None)

        if not isinstance(value, str) or not value.strip():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Workspace role is unavailable.",
            )

        return value.strip().lower()

    def _permissions(self) -> frozenset[str]:
        snapshot = getattr(
            self.scope,
            "effective_permissions",
            None,
        )

        if snapshot is not None:
            if not isinstance(snapshot, frozenset):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Workspace permissions are unavailable.",
                )

            return frozenset(
                permission
                for permission in snapshot
                if isinstance(permission, str)
                and permission in ALL_WORKSPACE_PERMISSIONS
            )

        # Compatibility for existing role-only callers.
        # Trusted tenant contexts supply resolved snapshots.
        return frozenset(
            WorkspacePermissionPolicy.permissions_for_role(
                self.role_key
            )
        )

    @staticmethod
    def _normalize(
        permissions: Iterable[str],
    ) -> frozenset[str]:
        return frozenset(
            permission.strip()
            for permission in permissions
            if isinstance(permission, str)
            and permission.strip()
        )

    def list(self) -> list[str]:
        return sorted(self._permissions())

    def list_permissions(self) -> list[str]:
        return self.list()

    def has(self, permission: str) -> bool:
        if not isinstance(permission, str):
            return False

        normalized = permission.strip()

        return bool(normalized) and normalized in self._permissions()

    def has_permission(self, permission: str) -> bool:
        return self.has(permission)

    def check_many(
        self,
        permissions: Iterable[str],
    ) -> dict[str, bool]:
        return {
            permission: self.has(permission)
            for permission in permissions
        }

    def require(self, permission: str) -> None:
        if self.has(permission):
            return

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Workspace permission required: {permission}",
        )

    def all(self, permissions: Iterable[str]) -> bool:
        return self._normalize(permissions).issubset(
            self._permissions()
        )

    def any(self, permissions: Iterable[str]) -> bool:
        return bool(
            self._normalize(permissions).intersection(
                self._permissions()
            )
        )

    def require_all(self, permissions: Iterable[str]) -> None:
        if self.all(permissions):
            return

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Required workspace permissions are missing.",
        )

    def require_any(self, permissions: Iterable[str]) -> None:
        if self.any(permissions):
            return

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "At least one required workspace permission "
                "is missing."
            ),
        )


__all__ = ["WorkspacePermissionService"]
