from __future__ import annotations

import uuid
from datetime import (
    datetime,
    timezone,
)

from app.core.redis import redis_client
from app.modules.channels.hardening import (
    PresenceLifetimeGuard,
    get_channel_hardening_settings,
)
from app.modules.channels.realtime_bus import (
    channel_realtime_bus,
)
from app.modules.channels.realtime_schemas import (
    WorkspaceChannelPresencePublic,
    WorkspaceChannelPresenceState,
    WorkspaceChannelRealtimeEventType,
    WorkspaceChannelTypingUser,
)


class WorkspaceChannelRealtimePresence:
    PRESENCE_PREFIX = (
        "workforce:channels:"
        "presence"
    )

    TYPING_PREFIX = (
        "workforce:channels:"
        "typing"
    )

    def __init__(
        self,
    ) -> None:
        settings = (
            get_channel_hardening_settings()
        )

        self.PRESENCE_TTL_SECONDS = (
            settings
            .presence_online_ttl_seconds
        )

        self.TYPING_TTL_SECONDS = (
            settings
            .typing_ttl_seconds
        )

        self.guard = PresenceLifetimeGuard(
            online_ttl_seconds=(
                settings
                .presence_online_ttl_seconds
            ),
            idle_after_seconds=(
                settings
                .presence_idle_after_seconds
            ),
            typing_ttl_seconds=(
                settings
                .typing_ttl_seconds
            ),
        )

    @classmethod
    def presence_key(
        cls,
        *,
        workspace_id: uuid.UUID,
        channel_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> str:
        return (
            f"{cls.PRESENCE_PREFIX}:"
            f"{workspace_id}:"
            f"{channel_id}:"
            f"{user_id}"
        )

    @classmethod
    def typing_key(
        cls,
        *,
        workspace_id: uuid.UUID,
        channel_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> str:
        return (
            f"{cls.TYPING_PREFIX}:"
            f"{workspace_id}:"
            f"{channel_id}:"
            f"{user_id}"
        )

    @staticmethod
    def _text(
        value,
    ) -> str | None:
        if value is None:
            return None

        if isinstance(
            value,
            bytes,
        ):
            return value.decode(
                "utf-8",
                errors="replace",
            )

        return str(value)

    async def heartbeat(
        self,
        *,
        workspace_id: uuid.UUID,
        channel_id: uuid.UUID,
        user_id: uuid.UUID,
        state:
            WorkspaceChannelPresenceState = (
                WorkspaceChannelPresenceState
                .ONLINE
            ),
    ) -> WorkspaceChannelPresencePublic:
        now = datetime.now(
            timezone.utc
        )

        key = self.presence_key(
            workspace_id=workspace_id,
            channel_id=channel_id,
            user_id=user_id,
        )

        await redis_client.hset(
            key,
            mapping={
                "status":
                    state.value,
                "last_seen_at":
                    now.isoformat(),
            },
        )

        await redis_client.expire(
            key,
            self.PRESENCE_TTL_SECONDS,
        )

        result = (
            WorkspaceChannelPresencePublic(
                user_id=user_id,
                status=state,
                last_seen_at=now,
            )
        )

        await channel_realtime_bus.publish(
            workspace_id=workspace_id,
            channel_id=channel_id,
            event_type=(
                WorkspaceChannelRealtimeEventType
                .PRESENCE_UPDATED
            ),
            actor_user_id=user_id,
            payload={
                "user_id":
                    str(user_id),
                "status":
                    state.value,
                "last_seen_at":
                    now.isoformat(),
            },
        )

        return result

    async def get_presence(
        self,
        *,
        workspace_id: uuid.UUID,
        channel_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> WorkspaceChannelPresencePublic:
        now = datetime.now(
            timezone.utc
        )

        key = self.presence_key(
            workspace_id=workspace_id,
            channel_id=channel_id,
            user_id=user_id,
        )

        raw = await redis_client.hgetall(
            key
        )

        if not raw:
            return (
                WorkspaceChannelPresencePublic(
                    user_id=user_id,
                    status=(
                        WorkspaceChannelPresenceState
                        .OFFLINE
                    ),
                    last_seen_at=now,
                )
            )

        normalized = {
            self._text(key):
                self._text(value)
            for key, value
            in raw.items()
        }

        raw_last_seen = normalized.get(
            "last_seen_at"
        )

        try:
            last_seen_at = (
                datetime.fromisoformat(
                    raw_last_seen
                )
                if raw_last_seen
                else now
            )

        except ValueError:
            last_seen_at = now

        evaluation = self.guard.evaluate(
            last_seen_at=last_seen_at,
            now=now,
        )

        if evaluation.stale:
            await redis_client.delete(
                key
            )

            status_value = (
                WorkspaceChannelPresenceState
                .OFFLINE
            )

        elif evaluation.idle:
            status_value = (
                WorkspaceChannelPresenceState
                .IDLE
            )

        else:
            raw_status = (
                normalized.get(
                    "status"
                )
                or (
                    WorkspaceChannelPresenceState
                    .ONLINE
                    .value
                )
            )

            try:
                status_value = (
                    WorkspaceChannelPresenceState(
                        raw_status
                    )
                )

            except ValueError:
                status_value = (
                    WorkspaceChannelPresenceState
                    .ONLINE
                )

        return (
            WorkspaceChannelPresencePublic(
                user_id=user_id,
                status=status_value,
                last_seen_at=(
                    last_seen_at
                ),
            )
        )

    async def disconnect(
        self,
        *,
        workspace_id: uuid.UUID,
        channel_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        await redis_client.delete(
            self.presence_key(
                workspace_id=workspace_id,
                channel_id=channel_id,
                user_id=user_id,
            )
        )

        now = datetime.now(
            timezone.utc
        )

        await channel_realtime_bus.publish(
            workspace_id=workspace_id,
            channel_id=channel_id,
            event_type=(
                WorkspaceChannelRealtimeEventType
                .PRESENCE_UPDATED
            ),
            actor_user_id=user_id,
            payload={
                "user_id":
                    str(user_id),
                "status":
                    (
                        WorkspaceChannelPresenceState
                        .OFFLINE
                        .value
                    ),
                "last_seen_at":
                    now.isoformat(),
            },
        )

    async def start_typing(
        self,
        *,
        workspace_id: uuid.UUID,
        channel_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> WorkspaceChannelTypingUser:
        now = datetime.now(
            timezone.utc
        )

        key = self.typing_key(
            workspace_id=workspace_id,
            channel_id=channel_id,
            user_id=user_id,
        )

        await redis_client.set(
            key,
            now.isoformat(),
            ex=self.TYPING_TTL_SECONDS,
        )

        await channel_realtime_bus.publish(
            workspace_id=workspace_id,
            channel_id=channel_id,
            event_type=(
                WorkspaceChannelRealtimeEventType
                .TYPING_STARTED
            ),
            actor_user_id=user_id,
            payload={
                "channel_id":
                    str(channel_id),
                "user_id":
                    str(user_id),
                "typing":
                    True,
            },
        )

        return (
            WorkspaceChannelTypingUser(
                user_id=user_id,
                channel_id=channel_id,
                started_at=now,
            )
        )

    async def typing_is_active(
        self,
        *,
        workspace_id: uuid.UUID,
        channel_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> bool:
        raw = await redis_client.get(
            self.typing_key(
                workspace_id=workspace_id,
                channel_id=channel_id,
                user_id=user_id,
            )
        )

        raw_text = self._text(
            raw
        )

        if not raw_text:
            return False

        try:
            started_at = (
                datetime.fromisoformat(
                    raw_text
                )
            )

        except ValueError:
            return False

        active = (
            self.guard
            .typing_is_active(
                typing_started_at=(
                    started_at
                )
            )
        )

        if not active:
            await redis_client.delete(
                self.typing_key(
                    workspace_id=workspace_id,
                    channel_id=channel_id,
                    user_id=user_id,
                )
            )

        return active

    async def stop_typing(
        self,
        *,
        workspace_id: uuid.UUID,
        channel_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        await redis_client.delete(
            self.typing_key(
                workspace_id=workspace_id,
                channel_id=channel_id,
                user_id=user_id,
            )
        )

        await channel_realtime_bus.publish(
            workspace_id=workspace_id,
            channel_id=channel_id,
            event_type=(
                WorkspaceChannelRealtimeEventType
                .TYPING_STOPPED
            ),
            actor_user_id=user_id,
            payload={
                "channel_id":
                    str(channel_id),
                "user_id":
                    str(user_id),
                "typing":
                    False,
            },
        )


channel_realtime_presence = (
    WorkspaceChannelRealtimePresence()
)


__all__ = [
    "WorkspaceChannelRealtimePresence",
    "channel_realtime_presence",
]