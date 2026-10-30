from __future__ import annotations

import json
import uuid
from datetime import (
    datetime,
    timezone,
)
from typing import Any

from app.core.redis import (
    redis_client,
)
from app.modules.channels.realtime_schemas import (
    WorkspaceChannelRealtimeEvent,
    WorkspaceChannelRealtimeEventType,
)


class WorkspaceChannelRealtimeBus:
    STREAM_LIMIT = 1000

    STREAM_TTL_SECONDS = (
        60 * 60 * 24
    )

    PUBSUB_PREFIX = (
        "workforce:channels:realtime"
    )

    STREAM_PREFIX = (
        "workforce:channels:events"
    )

    SEQUENCE_PREFIX = (
        "workforce:channels:sequence"
    )

    # =====================================================
    # KEYS
    # =====================================================

    @classmethod
    def stream_key(
        cls,
        *,
        workspace_id: uuid.UUID,
        channel_id: uuid.UUID,
    ) -> str:
        return (
            f"{cls.STREAM_PREFIX}:"
            f"{workspace_id}:"
            f"{channel_id}"
        )

    @classmethod
    def sequence_key(
        cls,
        *,
        workspace_id: uuid.UUID,
        channel_id: uuid.UUID,
    ) -> str:
        return (
            f"{cls.SEQUENCE_PREFIX}:"
            f"{workspace_id}:"
            f"{channel_id}"
        )

    @classmethod
    def pubsub_channel(
        cls,
        *,
        workspace_id: uuid.UUID,
        channel_id: uuid.UUID,
    ) -> str:
        return (
            f"{cls.PUBSUB_PREFIX}:"
            f"{workspace_id}:"
            f"{channel_id}"
        )

    # =====================================================
    # PUBLISH
    # =====================================================

    async def publish(
        self,
        *,
        workspace_id: uuid.UUID,
        channel_id: uuid.UUID,
        event_type:
            WorkspaceChannelRealtimeEventType,
        actor_user_id:
            uuid.UUID | None = None,
        payload:
            dict[str, Any] | None = None,
    ) -> WorkspaceChannelRealtimeEvent:
        sequence = await (
            redis_client.incr(
                self.sequence_key(
                    workspace_id=(
                        workspace_id
                    ),
                    channel_id=(
                        channel_id
                    ),
                )
            )
        )

        event = (
            WorkspaceChannelRealtimeEvent(
                event_id=uuid.uuid4(),
                event_type=event_type,
                workspace_id=workspace_id,
                channel_id=channel_id,
                actor_user_id=(
                    actor_user_id
                ),
                sequence=int(
                    sequence
                ),
                occurred_at=(
                    datetime.now(
                        timezone.utc
                    )
                ),
                payload=(
                    payload or {}
                ),
            )
        )

        encoded = (
            event.model_dump_json()
        )

        stream_key = (
            self.stream_key(
                workspace_id=(
                    workspace_id
                ),
                channel_id=(
                    channel_id
                ),
            )
        )

        await redis_client.rpush(
            stream_key,
            encoded,
        )

        await redis_client.ltrim(
            stream_key,
            -self.STREAM_LIMIT,
            -1,
        )

        await redis_client.expire(
            stream_key,
            self.STREAM_TTL_SECONDS,
        )

        await redis_client.expire(
            self.sequence_key(
                workspace_id=(
                    workspace_id
                ),
                channel_id=(
                    channel_id
                ),
            ),
            self.STREAM_TTL_SECONDS,
        )

        await redis_client.publish(
            self.pubsub_channel(
                workspace_id=(
                    workspace_id
                ),
                channel_id=(
                    channel_id
                ),
            ),
            encoded,
        )

        return event

    # =====================================================
    # REPLAY
    # =====================================================

    async def replay(
        self,
        *,
        workspace_id: uuid.UUID,
        channel_id: uuid.UUID,
        after_sequence: int,
        limit: int,
    ) -> list[
        WorkspaceChannelRealtimeEvent
    ]:
        raw_items = await (
            redis_client.lrange(
                self.stream_key(
                    workspace_id=(
                        workspace_id
                    ),
                    channel_id=(
                        channel_id
                    ),
                ),
                0,
                -1,
            )
        )

        events: list[
            WorkspaceChannelRealtimeEvent
        ] = []

        for raw in raw_items:
            try:
                event = (
                    WorkspaceChannelRealtimeEvent
                    .model_validate_json(
                        raw
                    )
                )
            except Exception:
                continue

            if (
                event.sequence
                <= after_sequence
            ):
                continue

            events.append(
                event
            )

            if (
                len(events)
                >= limit
            ):
                break

        return events

    # =====================================================
    # CURRENT SEQUENCE
    # =====================================================

    async def current_sequence(
        self,
        *,
        workspace_id: uuid.UUID,
        channel_id: uuid.UUID,
    ) -> int:
        raw = await redis_client.get(
            self.sequence_key(
                workspace_id=(
                    workspace_id
                ),
                channel_id=(
                    channel_id
                ),
            )
        )

        if raw is None:
            return 0

        return int(
            raw
        )


channel_realtime_bus = (
    WorkspaceChannelRealtimeBus()
)


__all__ = [
    "WorkspaceChannelRealtimeBus",
    "channel_realtime_bus",
]