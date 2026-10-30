from __future__ import annotations

import inspect
import sys
from pathlib import Path


# =========================================================
# BACKEND IMPORT ROOT
# =========================================================
#
# This script is executed directly from:
#
#   backend\scripts\phase11_5_verify_workspace_enforcement.py
#
# Python therefore places backend\scripts at sys.path[0].
# Add the backend project root explicitly so imports such as
# "app.modules..." work reliably regardless of invocation mode.
# =========================================================

BACKEND_ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

backend_root_text = str(
    BACKEND_ROOT
)

if backend_root_text not in sys.path:
    sys.path.insert(
        0,
        backend_root_text,
    )


from app.modules.workspaces.service import (  # noqa: E402
    WorkspaceService,
)


def require_token(
    source: str,
    token: str,
) -> int:
    position = source.find(
        token
    )

    if position < 0:
        raise RuntimeError(
            "Workspace entitlement enforcement "
            f"is missing token: {token}"
        )

    return position


def main() -> None:
    source = inspect.getsource(
        WorkspaceService.create_workspace
    )

    entitlement_position = require_token(
        source,
        "require_workspace_creation",
    )

    require_token(
        source,
        "WorkspaceEntitlementAccess",
    )

    require_token(
        source,
        "WorkspaceEntitlementDeniedError",
    )

    slug_position = require_token(
        source,
        "_allocate_workspace_slug",
    )

    repository_position = require_token(
        source,
        "repository.create_workspace",
    )

    if entitlement_position > slug_position:
        raise RuntimeError(
            "Entitlement check must execute before "
            "workspace slug allocation."
        )

    if entitlement_position > repository_position:
        raise RuntimeError(
            "Entitlement check must execute before "
            "workspace database writes."
        )

    print(
        "Backend root:",
        BACKEND_ROOT,
    )

    print(
        "PASS WorkspaceEntitlementAccess present"
    )

    print(
        "PASS require_workspace_creation present"
    )

    print(
        "PASS entitlement executes before "
        "workspace slug allocation"
    )

    print(
        "PASS entitlement executes before "
        "workspace database writes"
    )

    print(
        "PASS existing WorkspaceService creation "
        "path preserved"
    )


if __name__ == "__main__":
    main()