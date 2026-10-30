from __future__ import annotations

import logging
import uuid
from collections.abc import Iterable

from app.modules.channels.realtime_events import (
    channel_realtime_events,
)


logger = logging.getLogger(
    __name__
)


class WorkspaceChannelRealtimeAttachmentBridge:
    """
    Publishes channel attachment-binding realtime events.

    The attachment mutation must already be successfully
    persisted before this bridge is called.

    Realtime publication is deliberately best-effort:
    a Redis/WebSocket publication failure must never undo
    a successful attachment database mutation.
    """

    async def publish_bound(
        self,
        *,
        workspace_id: uuid.UUID,
        channel_id: uuid.UUID,
        message_id: uuid.UUID,
        attachment_ids: Iterable[
            uuid.UUID
        ],
        actor_user_id: uuid.UUID,
    ) -> None:
        normalized = list(
            dict.fromkeys(
                attachment_ids
            )
        )

        if not normalized:
            return

        try:
            await (
                channel_realtime_events
                .attachment_bound(
                    workspace_id=workspace_id,
                    channel_id=channel_id,
                    message_id=message_id,
                    attachment_ids=normalized,
                    actor_user_id=actor_user_id,
                )
            )

        except Exception:
            logger.exception(
                "channel_attachment_realtime_publish_failed "
                "workspace_id=%s "
                "channel_id=%s "
                "message_id=%s "
                "attachment_count=%s",
                workspace_id,
                channel_id,
                message_id,
                len(
                    normalized
                ),
            )


channel_realtime_attachment_bridge = (
    WorkspaceChannelRealtimeAttachmentBridge()
)


__all__ = [
    "WorkspaceChannelRealtimeAttachmentBridge",
    "channel_realtime_attachment_bridge",
]