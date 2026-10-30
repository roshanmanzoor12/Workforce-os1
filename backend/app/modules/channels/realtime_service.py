from __future__ import annotations

import uuid
from datetime import (
    datetime,
    timezone,
)
from typing import Any

from fastapi import (
    HTTPException,
    status,
)
from sqlalchemy import select

from app.core.redis import redis_client
from app.modules.channels.hardening import (
    ChannelAccessDenied,
    ChannelAccessGuard,
    ChannelRateLimiter,
    get_channel_hardening_settings,
)
from app.modules.channels.models import (
    WorkspaceChannel,
)
from app.modules.channels.realtime_bus import (
    channel_realtime_bus,
)
from app.modules.channels.realtime_presence import (
    channel_realtime_presence,
)
from app.modules.channels.realtime_replay import (
    ChannelRealtimeReplayPolicy,
    ReplayWindowExceeded,
)
from app.modules.channels.realtime_schemas import (
    WorkspaceChannelHeartbeatResponse,
    WorkspaceChannelPresenceState,
    WorkspaceChannelRealtimeActionResponse,
    WorkspaceChannelRealtimeCapabilities,
    WorkspaceChannelRealtimeEventPage,
    WorkspaceChannelRealtimeEventType,
    WorkspaceChannelRealtimeResumeRequest,
    WorkspaceChannelRealtimeTicketResponse,
)
from app.modules.channels.realtime_ticket import (
    channel_realtime_ticket_service,
)
from app.modules.workspace_permissions.permissions import (
    WorkspacePermission,
)
from app.modules.workspace_search.access import (
    resolve_search_access,
)


class WorkspaceChannelRealtimeNotFoundError(
    LookupError
):
    pass


class WorkspaceChannelRealtimePermissionError(
    PermissionError
):
    pass


class WorkspaceChannelRealtimeService:
    def __init__(
        self,
    ) -> None:
        self.settings = (
            get_channel_hardening_settings()
        )

        self.rate_limiter = (
            ChannelRateLimiter(
                redis_client
            )
        )

        self.replay_policy = (
            ChannelRealtimeReplayPolicy(
                batch_size=(
                    self.settings
                    .replay_batch_size
                ),
                max_events=(
                    self.settings
                    .replay_max_events
                ),
            )
        )

    async def resolve_access(
        self,
        *,
        workspace_id: uuid.UUID,
        context: Any,
    ):
        access = await (
            resolve_search_access(
                workspace_id=(
                    workspace_id
                ),
                context=context,
            )
        )

        permissions = set(
            access.permissions
        )

        if (
            WorkspacePermission
            .CHANNELS_READ
            .value
            not in permissions
        ):
            raise (
                WorkspaceChannelRealtimePermissionError(
                    "Channel read permission "
                    "is required."
                )
            )

        return access

    async def require_channel(
        self,
        *,
        workspace_id: uuid.UUID,
        channel_id: uuid.UUID,
        context: Any,
    ) -> WorkspaceChannel:
        result = await (
            context
            .control_session
            .execute(
                select(
                    WorkspaceChannel
                ).where(
                    WorkspaceChannel.id
                    == channel_id,
                    WorkspaceChannel.workspace_id
                    == workspace_id,
                )
            )
        )

        channel = (
            result.scalar_one_or_none()
        )

        if (
            channel is None
            or not channel.is_active
        ):
            raise (
                WorkspaceChannelRealtimeNotFoundError(
                    "Workspace channel "
                    "not found."
                )
            )

        return channel

    async def require_member(
        self,
        *,
        workspace_id: uuid.UUID,
        channel_id: uuid.UUID,
        user_id: uuid.UUID,
        context: Any,
    ) -> None:
        guard = ChannelAccessGuard(
            context.control_session
        )

        try:
            await guard.assert_access(
                workspace_id=workspace_id,
                channel_id=channel_id,
                user_id=user_id,
            )

        except ChannelAccessDenied as exc:
            raise (
                WorkspaceChannelRealtimePermissionError(
                    "Active channel membership "
                    "is required."
                )
            ) from exc

    async def _rate_limit(
        self,
        *,
        bucket: str,
        workspace_id: uuid.UUID,
        channel_id: uuid.UUID,
        user_id: uuid.UUID,
        limit: int,
        window_seconds: int,
    ) -> None:
        decision = await (
            self.rate_limiter.check(
                bucket=bucket,
                workspace_id=workspace_id,
                channel_id=channel_id,
                user_id=user_id,
                limit=limit,
                window_seconds=(
                    window_seconds
                ),
            )
        )

        if decision.allowed:
            return

        raise HTTPException(
            status_code=(
                status.HTTP_429_TOO_MANY_REQUESTS
            ),
            detail=(
                "Realtime action rate "
                "limit exceeded."
            ),
            headers={
                "Retry-After": str(
                    decision
                    .retry_after_seconds
                ),
            },
        )

    async def ticket(
        self,
        *,
        workspace_id: uuid.UUID,
        channel_id: uuid.UUID,
        context: Any,
    ) -> WorkspaceChannelRealtimeTicketResponse:
        access = await self.resolve_access(
            workspace_id=workspace_id,
            context=context,
        )

        await self.require_channel(
            workspace_id=workspace_id,
            channel_id=channel_id,
            context=context,
        )

        await self.require_member(
            workspace_id=workspace_id,
            channel_id=channel_id,
            user_id=(
                access.actor_user_id
            ),
            context=context,
        )

        await self._rate_limit(
            bucket="ticket",
            workspace_id=workspace_id,
            channel_id=channel_id,
            user_id=(
                access.actor_user_id
            ),
            limit=(
                self.settings
                .websocket_connect_limit
            ),
            window_seconds=(
                self.settings
                .websocket_connect_window_seconds
            ),
        )

        ticket, ttl = await (
            channel_realtime_ticket_service
            .create(
                workspace_id=workspace_id,
                channel_id=channel_id,
                user_id=(
                    access.actor_user_id
                ),
            )
        )

        return (
            WorkspaceChannelRealtimeTicketResponse(
                ticket=ticket,
                expires_in_seconds=ttl,
            )
        )

    async def resume(
        self,
        *,
        workspace_id: uuid.UUID,
        payload:
            WorkspaceChannelRealtimeResumeRequest,
        context: Any,
    ) -> WorkspaceChannelRealtimeEventPage:
        access = await self.resolve_access(
            workspace_id=workspace_id,
            context=context,
        )

        await self.require_channel(
            workspace_id=workspace_id,
            channel_id=payload.channel_id,
            context=context,
        )

        await self.require_member(
            workspace_id=workspace_id,
            channel_id=payload.channel_id,
            user_id=(
                access.actor_user_id
            ),
            context=context,
        )

        current_sequence = await (
            channel_realtime_bus
            .current_sequence(
                workspace_id=workspace_id,
                channel_id=(
                    payload.channel_id
                ),
            )
        )

        try:
            replay_limit = (
                self.replay_policy
                .validate(
                    after_sequence=(
                        payload.after_sequence
                    ),
                    current_sequence=(
                        current_sequence
                    ),
                    requested_limit=(
                        payload.limit
                    ),
                )
            )

        except ReplayWindowExceeded as exc:
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=str(exc),
            ) from exc

        events = await (
            channel_realtime_bus.replay(
                workspace_id=workspace_id,
                channel_id=(
                    payload.channel_id
                ),
                after_sequence=(
                    payload.after_sequence
                ),
                limit=replay_limit,
            )
        )

        if events:
            next_sequence = (
                events[-1].sequence
            )
        else:
            next_sequence = (
                payload.after_sequence
            )

        has_more = (
            next_sequence
            < current_sequence
        )

        return (
            WorkspaceChannelRealtimeEventPage(
                channel_id=(
                    payload.channel_id
                ),
                events=events,
                next_sequence=(
                    next_sequence
                ),
                has_more=has_more,
            )
        )

    async def start_typing(
        self,
        *,
        workspace_id: uuid.UUID,
        channel_id: uuid.UUID,
        context: Any,
    ) -> WorkspaceChannelRealtimeActionResponse:
        access = await self.resolve_access(
            workspace_id=workspace_id,
            context=context,
        )

        await self.require_channel(
            workspace_id=workspace_id,
            channel_id=channel_id,
            context=context,
        )

        await self.require_member(
            workspace_id=workspace_id,
            channel_id=channel_id,
            user_id=(
                access.actor_user_id
            ),
            context=context,
        )

        await self._rate_limit(
            bucket="typing",
            workspace_id=workspace_id,
            channel_id=channel_id,
            user_id=(
                access.actor_user_id
            ),
            limit=(
                self.settings
                .typing_event_limit
            ),
            window_seconds=(
                self.settings
                .typing_event_window_seconds
            ),
        )

        await (
            channel_realtime_presence
            .start_typing(
                workspace_id=workspace_id,
                channel_id=channel_id,
                user_id=(
                    access.actor_user_id
                ),
            )
        )

        return (
            WorkspaceChannelRealtimeActionResponse(
                success=True
            )
        )

    async def stop_typing(
        self,
        *,
        workspace_id: uuid.UUID,
        channel_id: uuid.UUID,
        context: Any,
    ) -> WorkspaceChannelRealtimeActionResponse:
        access = await self.resolve_access(
            workspace_id=workspace_id,
            context=context,
        )

        await self.require_channel(
            workspace_id=workspace_id,
            channel_id=channel_id,
            context=context,
        )

        await self.require_member(
            workspace_id=workspace_id,
            channel_id=channel_id,
            user_id=(
                access.actor_user_id
            ),
            context=context,
        )

        await self._rate_limit(
            bucket="typing",
            workspace_id=workspace_id,
            channel_id=channel_id,
            user_id=(
                access.actor_user_id
            ),
            limit=(
                self.settings
                .typing_event_limit
            ),
            window_seconds=(
                self.settings
                .typing_event_window_seconds
            ),
        )

        await (
            channel_realtime_presence
            .stop_typing(
                workspace_id=workspace_id,
                channel_id=channel_id,
                user_id=(
                    access.actor_user_id
                ),
            )
        )

        return (
            WorkspaceChannelRealtimeActionResponse(
                success=True
            )
        )

    async def heartbeat(
        self,
        *,
        workspace_id: uuid.UUID,
        channel_id: uuid.UUID,
        context: Any,
    ) -> WorkspaceChannelHeartbeatResponse:
        access = await self.resolve_access(
            workspace_id=workspace_id,
            context=context,
        )

        await self.require_channel(
            workspace_id=workspace_id,
            channel_id=channel_id,
            context=context,
        )

        await self.require_member(
            workspace_id=workspace_id,
            channel_id=channel_id,
            user_id=(
                access.actor_user_id
            ),
            context=context,
        )

        await self._rate_limit(
            bucket="heartbeat",
            workspace_id=workspace_id,
            channel_id=channel_id,
            user_id=(
                access.actor_user_id
            ),
            limit=(
                self.settings
                .heartbeat_limit
            ),
            window_seconds=(
                self.settings
                .heartbeat_window_seconds
            ),
        )

        await (
            channel_realtime_presence
            .heartbeat(
                workspace_id=workspace_id,
                channel_id=channel_id,
                user_id=(
                    access.actor_user_id
                ),
                state=(
                    WorkspaceChannelPresenceState
                    .ONLINE
                ),
            )
        )

        return (
            WorkspaceChannelHeartbeatResponse(
                success=True,
                workspace_id=workspace_id,
                actor_user_id=(
                    access.actor_user_id
                ),
                timestamp=(
                    datetime.now(
                        timezone.utc
                    )
                ),
            )
        )

    async def message_created(
        self,
        *,
        workspace_id: uuid.UUID,
        channel_id: uuid.UUID,
        actor_user_id:
            uuid.UUID | None,
        payload: dict[str, Any],
    ):
        return await (
            channel_realtime_bus.publish(
                workspace_id=workspace_id,
                channel_id=channel_id,
                event_type=(
                    WorkspaceChannelRealtimeEventType
                    .MESSAGE_CREATED
                ),
                actor_user_id=(
                    actor_user_id
                ),
                payload=payload,
            )
        )

    async def message_updated(
        self,
        *,
        workspace_id: uuid.UUID,
        channel_id: uuid.UUID,
        actor_user_id:
            uuid.UUID | None,
        payload: dict[str, Any],
    ):
        return await (
            channel_realtime_bus.publish(
                workspace_id=workspace_id,
                channel_id=channel_id,
                event_type=(
                    WorkspaceChannelRealtimeEventType
                    .MESSAGE_UPDATED
                ),
                actor_user_id=(
                    actor_user_id
                ),
                payload=payload,
            )
        )

    async def message_deleted(
        self,
        *,
        workspace_id: uuid.UUID,
        channel_id: uuid.UUID,
        actor_user_id:
            uuid.UUID | None,
        payload: dict[str, Any],
    ):
        return await (
            channel_realtime_bus.publish(
                workspace_id=workspace_id,
                channel_id=channel_id,
                event_type=(
                    WorkspaceChannelRealtimeEventType
                    .MESSAGE_DELETED
                ),
                actor_user_id=(
                    actor_user_id
                ),
                payload=payload,
            )
        )

    async def attachment_bound(
        self,
        *,
        workspace_id: uuid.UUID,
        channel_id: uuid.UUID,
        actor_user_id:
            uuid.UUID | None,
        payload: dict[str, Any],
    ):
        return await (
            channel_realtime_bus.publish(
                workspace_id=workspace_id,
                channel_id=channel_id,
                event_type=(
                    WorkspaceChannelRealtimeEventType
                    .ATTACHMENT_BOUND
                ),
                actor_user_id=(
                    actor_user_id
                ),
                payload=payload,
            )
        )

    @staticmethod
    def capabilities(
    ) -> WorkspaceChannelRealtimeCapabilities:
        return (
            WorkspaceChannelRealtimeCapabilities()
        )


channel_realtime_service = (
    WorkspaceChannelRealtimeService()
)


__all__ = [
    "WorkspaceChannelRealtimeNotFoundError",
    "WorkspaceChannelRealtimePermissionError",
    "WorkspaceChannelRealtimeService",
    "channel_realtime_service",
]