from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from app.core.exceptions import ValidationError
from app.modules.workspace_permissions.permissions import (
    WorkspacePermission,
)
from app.modules.workspace_search.access import (
    resolve_search_access,
)


@dataclass(
    frozen=True,
    slots=True,
)
class VoiceChannelAccess:
    workspace_id: uuid.UUID

    actor_user_id: uuid.UUID

    permissions: frozenset[str]

    can_read: bool

    can_moderate: bool


async def resolve_voice_channel_access(
    *,
    workspace_id: uuid.UUID,
    context: Any,
) -> VoiceChannelAccess:
    base = await resolve_search_access(
        workspace_id=workspace_id,
        context=context,
    )

    permissions = frozenset(
        base.permissions
    )

    can_read = (
        WorkspacePermission
        .CHANNELS_READ
        .value
        in permissions
    )

    can_moderate = (
        WorkspacePermission
        .CHANNELS_MANAGE
        .value
        in permissions
    )

    if not can_read and not can_moderate:
        raise ValidationError(
            "Channel read permission required."
        )

    return VoiceChannelAccess(
        workspace_id=workspace_id,

        actor_user_id=(
            base.actor_user_id
        ),

        permissions=permissions,

        can_read=can_read,

        can_moderate=can_moderate,
    )


def require_voice_moderator(
    access: VoiceChannelAccess,
) -> None:
    if not access.can_moderate:
        raise ValidationError(
            "Channel moderation permission required."
        )


__all__ = [
    "VoiceChannelAccess",
    "resolve_voice_channel_access",
    "require_voice_moderator",
]