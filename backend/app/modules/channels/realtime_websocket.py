from __future__ import annotations

import asyncio
import json
import uuid
from contextlib import suppress

from fastapi import (
    WebSocket,
    WebSocketDisconnect,
)

from app.core.database import (
    ControlSessionLocal,
)
from app.core.redis import (
    redis_client,
)
from app.modules.channels.hardening import (
    ChannelAccessDenied,
    ChannelAccessGuard,
    ChannelRateLimiter,
    channel_realtime_metrics,
    get_channel_hardening_settings,
)
from app.modules.channels.realtime_bus import (
    channel_realtime_bus,
)
from app.modules.channels.realtime_presence import (
    channel_realtime_presence,
)
from app.modules.channels.realtime_pubsub import (
    ChannelRealtimePubSubSession,
)
from app.modules.channels.realtime_schemas import (
    WorkspaceChannelPresenceState,
    WorkspaceChannelRealtimeEventType,
)
from app.modules.channels.realtime_ticket import (
    WorkspaceChannelRealtimeIdentity,
    channel_realtime_ticket_service,
)


class WorkspaceChannelRealtimeWebSocket:
    """
    Hardened authenticated workspace-channel WebSocket.

    Security properties:

    - one-use ticket authentication;
    - active membership checked before accept;
    - membership periodically revalidated;
    - heartbeat / typing actions rate limited;
    - Redis pubsub always unsubscribed and closed;
    - presence and typing state cleaned on disconnect.
    """

    RECEIVE_TIMEOUT_SECONDS = 15

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

    async def _assert_access(
        self,
        *,
        identity:
            WorkspaceChannelRealtimeIdentity,
    ) -> None:
        if not (
            self.settings
            .require_membership_revalidation
        ):
            return

        try:
            async with (
                ControlSessionLocal()
                as session
            ):
                guard = (
                    ChannelAccessGuard(
                        session
                    )
                )

                await guard.assert_access(
                    workspace_id=(
                        identity.workspace_id
                    ),
                    channel_id=(
                        identity.channel_id
                    ),
                    user_id=(
                        identity.user_id
                    ),
                )

        except ChannelAccessDenied:
            raise

        except Exception:
            channel_realtime_metrics.increment(
                "websocket.access_check_error"
            )

            if (
                self.settings
                .fail_closed_on_access_error
            ):
                raise ChannelAccessDenied(
                    "Unable to verify "
                    "channel membership."
                )

    async def _check_limit(
        self,
        *,
        bucket: str,
        identity:
            WorkspaceChannelRealtimeIdentity,
        limit: int,
        window_seconds: int,
    ) -> bool:
        decision = await (
            self.rate_limiter.check(
                bucket=bucket,
                workspace_id=(
                    identity.workspace_id
                ),
                channel_id=(
                    identity.channel_id
                ),
                user_id=(
                    identity.user_id
                ),
                limit=limit,
                window_seconds=(
                    window_seconds
                ),
            )
        )

        if decision.allowed:
            return True

        channel_realtime_metrics.increment(
            f"rate_limit.{bucket}.blocked"
        )

        return False

    async def connect(
        self,
        *,
        websocket: WebSocket,
        ticket: str,
    ) -> None:
        identity = await (
            channel_realtime_ticket_service
            .consume(
                ticket=ticket
            )
        )

        if identity is None:
            await websocket.close(
                code=4401,
                reason=(
                    "Invalid or expired "
                    "realtime ticket."
                ),
            )

            return

        allowed = await self._check_limit(
            bucket="websocket_connect",
            identity=identity,
            limit=(
                self.settings
                .websocket_connect_limit
            ),
            window_seconds=(
                self.settings
                .websocket_connect_window_seconds
            ),
        )

        if not allowed:
            await websocket.close(
                code=4429,
                reason=(
                    "Realtime connection "
                    "rate limit exceeded."
                ),
            )

            return

        try:
            await self._assert_access(
                identity=identity
            )

        except ChannelAccessDenied:
            channel_realtime_metrics.increment(
                "websocket.access_denied"
            )

            await websocket.close(
                code=4403,
                reason=(
                    "Active channel membership "
                    "is required."
                ),
            )

            return

        await websocket.accept()

        channel_realtime_metrics.increment(
            "websocket.connected"
        )

        try:
            await self._run(
                websocket=websocket,
                identity=identity,
            )

        finally:
            channel_realtime_metrics.increment(
                "websocket.closed"
            )

    async def _run(
        self,
        *,
        websocket: WebSocket,
        identity:
            WorkspaceChannelRealtimeIdentity,
    ) -> None:
        redis_channel = (
            channel_realtime_bus
            .pubsub_channel(
                workspace_id=(
                    identity.workspace_id
                ),
                channel_id=(
                    identity.channel_id
                ),
            )
        )

        pubsub_session = (
            ChannelRealtimePubSubSession(
                redis=redis_client,
                channel=redis_channel,
            )
        )

        await pubsub_session.open()

        await (
            channel_realtime_presence
            .heartbeat(
                workspace_id=(
                    identity.workspace_id
                ),
                channel_id=(
                    identity.channel_id
                ),
                user_id=(
                    identity.user_id
                ),
                state=(
                    WorkspaceChannelPresenceState
                    .ONLINE
                ),
            )
        )

        connected_event = await (
            channel_realtime_bus.publish(
                workspace_id=(
                    identity.workspace_id
                ),
                channel_id=(
                    identity.channel_id
                ),
                event_type=(
                    WorkspaceChannelRealtimeEventType
                    .CONNECTED
                ),
                actor_user_id=(
                    identity.user_id
                ),
                payload={
                    "user_id": str(
                        identity.user_id
                    ),
                },
            )
        )

        await websocket.send_text(
            connected_event
            .model_dump_json()
        )

        sender_task = (
            asyncio.create_task(
                self._redis_to_websocket(
                    websocket=websocket,
                    pubsub_session=(
                        pubsub_session
                    ),
                )
            )
        )

        receiver_task = (
            asyncio.create_task(
                self._websocket_receiver(
                    websocket=websocket,
                    identity=identity,
                )
            )
        )

        try:
            done, pending = await (
                asyncio.wait(
                    {
                        sender_task,
                        receiver_task,
                    },
                    return_when=(
                        asyncio.FIRST_COMPLETED
                    ),
                )
            )

            for task in pending:
                task.cancel()

            for task in pending:
                with suppress(
                    asyncio.CancelledError
                ):
                    await task

            for task in done:
                if task.cancelled():
                    continue

                exception = (
                    task.exception()
                )

                if exception is not None:
                    raise exception

        except (
            WebSocketDisconnect,
            asyncio.CancelledError,
        ):
            pass

        except Exception:
            channel_realtime_metrics.increment(
                "websocket.session_error"
            )

        finally:
            sender_task.cancel()
            receiver_task.cancel()

            for task in (
                sender_task,
                receiver_task,
            ):
                with suppress(
                    asyncio.CancelledError,
                    Exception,
                ):
                    await task

            with suppress(
                Exception
            ):
                await (
                    channel_realtime_presence
                    .stop_typing(
                        workspace_id=(
                            identity.workspace_id
                        ),
                        channel_id=(
                            identity.channel_id
                        ),
                        user_id=(
                            identity.user_id
                        ),
                    )
                )

            with suppress(
                Exception
            ):
                await (
                    channel_realtime_presence
                    .disconnect(
                        workspace_id=(
                            identity.workspace_id
                        ),
                        channel_id=(
                            identity.channel_id
                        ),
                        user_id=(
                            identity.user_id
                        ),
                    )
                )

            with suppress(
                Exception
            ):
                await (
                    channel_realtime_bus
                    .publish(
                        workspace_id=(
                            identity.workspace_id
                        ),
                        channel_id=(
                            identity.channel_id
                        ),
                        event_type=(
                            WorkspaceChannelRealtimeEventType
                            .DISCONNECTED
                        ),
                        actor_user_id=(
                            identity.user_id
                        ),
                        payload={
                            "user_id": str(
                                identity.user_id
                            ),
                        },
                    )
                )

            await pubsub_session.close()

            with suppress(
                Exception
            ):
                await websocket.close()

    async def _redis_to_websocket(
        self,
        *,
        websocket: WebSocket,
        pubsub_session:
            ChannelRealtimePubSubSession,
    ) -> None:
        while True:
            data = await (
                pubsub_session
                .next_payload(
                    timeout=1.0
                )
            )

            if data is None:
                await asyncio.sleep(
                    0.05
                )

                continue

            await websocket.send_text(
                data
            )

    async def _send_rate_limit(
        self,
        *,
        websocket: WebSocket,
        action: str,
    ) -> None:
        with suppress(
            Exception
        ):
            await websocket.send_text(
                json.dumps(
                    {
                        "type":
                            "realtime.rate_limited",
                        "action":
                            action,
                    },
                    separators=(
                        ",",
                        ":",
                    ),
                )
            )

    async def _websocket_receiver(
        self,
        *,
        websocket: WebSocket,
        identity:
            WorkspaceChannelRealtimeIdentity,
    ) -> None:
        while True:
            try:
                raw = await (
                    asyncio.wait_for(
                        websocket.receive_text(),
                        timeout=(
                            self
                            .RECEIVE_TIMEOUT_SECONDS
                        ),
                    )
                )

            except asyncio.TimeoutError:
                try:
                    await self._assert_access(
                        identity=identity
                    )

                except ChannelAccessDenied:
                    await websocket.close(
                        code=4403,
                        reason=(
                            "Channel membership "
                            "is no longer active."
                        ),
                    )

                    return

                await (
                    channel_realtime_presence
                    .heartbeat(
                        workspace_id=(
                            identity.workspace_id
                        ),
                        channel_id=(
                            identity.channel_id
                        ),
                        user_id=(
                            identity.user_id
                        ),
                    )
                )

                continue

            await self._assert_access(
                identity=identity
            )

            try:
                payload = json.loads(
                    raw
                )

            except json.JSONDecodeError:
                continue

            if not isinstance(
                payload,
                dict,
            ):
                continue

            action = payload.get(
                "action"
            )

            if action == "heartbeat":
                allowed = (
                    await self._check_limit(
                        bucket="heartbeat",
                        identity=identity,
                        limit=(
                            self.settings
                            .heartbeat_limit
                        ),
                        window_seconds=(
                            self.settings
                            .heartbeat_window_seconds
                        ),
                    )
                )

                if not allowed:
                    await self._send_rate_limit(
                        websocket=websocket,
                        action=action,
                    )

                    continue

                await (
                    channel_realtime_presence
                    .heartbeat(
                        workspace_id=(
                            identity.workspace_id
                        ),
                        channel_id=(
                            identity.channel_id
                        ),
                        user_id=(
                            identity.user_id
                        ),
                    )
                )

                continue

            if action == "typing.start":
                allowed = (
                    await self._check_limit(
                        bucket="typing",
                        identity=identity,
                        limit=(
                            self.settings
                            .typing_event_limit
                        ),
                        window_seconds=(
                            self.settings
                            .typing_event_window_seconds
                        ),
                    )
                )

                if not allowed:
                    await self._send_rate_limit(
                        websocket=websocket,
                        action=action,
                    )

                    continue

                await (
                    channel_realtime_presence
                    .start_typing(
                        workspace_id=(
                            identity.workspace_id
                        ),
                        channel_id=(
                            identity.channel_id
                        ),
                        user_id=(
                            identity.user_id
                        ),
                    )
                )

                continue

            if action == "typing.stop":
                allowed = (
                    await self._check_limit(
                        bucket="typing",
                        identity=identity,
                        limit=(
                            self.settings
                            .typing_event_limit
                        ),
                        window_seconds=(
                            self.settings
                            .typing_event_window_seconds
                        ),
                    )
                )

                if not allowed:
                    await self._send_rate_limit(
                        websocket=websocket,
                        action=action,
                    )

                    continue

                await (
                    channel_realtime_presence
                    .stop_typing(
                        workspace_id=(
                            identity.workspace_id
                        ),
                        channel_id=(
                            identity.channel_id
                        ),
                        user_id=(
                            identity.user_id
                        ),
                    )
                )


channel_realtime_websocket = (
    WorkspaceChannelRealtimeWebSocket()
)


__all__ = [
    "WorkspaceChannelRealtimeWebSocket",
    "channel_realtime_websocket",
]