from __future__ import annotations

from dataclasses import dataclass

from .entitlements import AccountEntitlements


@dataclass(
    frozen=True,
    slots=True,
)
class WorkspaceCreationDecision:
    allowed: bool
    reason: str | None

    workspace_limit: int | None
    workspace_count: int


def build_workspace_creation_decision(
    entitlements: AccountEntitlements,
) -> WorkspaceCreationDecision:
    if entitlements.create_workspace:
        return WorkspaceCreationDecision(
            allowed=True,
            reason=None,
            workspace_limit=(
                entitlements.workspace_limit
            ),
            workspace_count=(
                entitlements.workspace_count
            ),
        )

    if entitlements.workspace_limit is not None and entitlements.workspace_limit <= 0:
        reason = (
            "Current plan does not include "
            "workspace creation."
        )

    elif (
        entitlements.workspace_limit is not None
        and entitlements.workspace_count >= entitlements.workspace_limit
    ):
        reason = (
            "Workspace limit reached for "
            "the current plan."
        )

    else:
        reason = (
            "Current subscription is not active "
            "for workspace creation."
        )

    return WorkspaceCreationDecision(
        allowed=False,
        reason=reason,
        workspace_limit=(
            entitlements.workspace_limit
        ),
        workspace_count=(
            entitlements.workspace_count
        ),
    )


__all__ = [
    "WorkspaceCreationDecision",
    "build_workspace_creation_decision",
]
