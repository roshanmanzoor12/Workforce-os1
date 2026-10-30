from __future__ import annotations

from fastapi import HTTPException

from app.modules.workspace_permissions.service import (
    WorkspacePermissionService,
)


API_KEYS_MANAGE_PERMISSION = "integrations.manage"

# Initial external access is deliberately limited to read scopes.
# Add scopes here when their external API authorization is implemented.
ALLOWED_API_KEY_SCOPES = frozenset(
    {
        "employees.read",
        "reports.self.read",
        "analytics.self.read",
    }
)


def require_api_key_management(scope: object) -> None:
    WorkspacePermissionService(scope).require(
        API_KEYS_MANAGE_PERMISSION
    )


def require_grantable_scopes(
    scope: object,
    scopes: list[str],
) -> None:
    unknown = set(scopes) - ALLOWED_API_KEY_SCOPES

    if unknown:
        raise HTTPException(
            status_code=422,
            detail="Unsupported API key scopes: "
            + ", ".join(sorted(unknown)),
        )

    permissions = WorkspacePermissionService(scope)

    # An issuer cannot grant permissions they do not possess.
    for permission in scopes:
        permissions.require(permission)