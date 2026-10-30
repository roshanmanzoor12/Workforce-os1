from __future__ import annotations

import asyncio
import json
import logging
import os
import uuid
from typing import Any

from redis.exceptions import RedisError
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
)

from .realtime_bus import (
    CHAT_REALTIME_CHANNEL,
    ChatRealtimeBus,
)
from .realtime_dispatcher import ChatRealtimeDispatcher
from .realtime_events import ChatRealtimeEvent


logger = logging.getLogger(__name__)


class ChatRealtimeSubscriber:
    def __init__(
        self,
        *,
        redis_client: Any,
        session_factory: async_sessionmaker[AsyncSession],
        dispatcher: ChatRealtimeDispatcher | None = None,
        channel: str = CHAT_REALTIME_CHANNEL,
        bridge_channel: str | None = None,
    ) -> None:
        self.redis_client = redis_client
        self.session_factory = session_factory

        self.dispatcher = (
            dispatcher
            or ChatRealtimeDispatcher()
        )

        self.channel = channel

        self.bridge_channel = (
            bridge_channel
            if bridge_channel is not None
            else os.getenv("WORKFORCE_REALTIME_CHANNEL")
            or "workforce:realtime:events"
        )

        if self.bridge_channel == self.channel:
            raise ValueError(
                "Chat and bridge channels must use different names."
            )

        self._channels = tuple(
            dict.fromkeys(
                (
                    self.channel,
                    self.bridge_channel,
                )
            )
        )

        self._stopping = asyncio.Event()

    async def stop(self) -> None:
        self._stopping.set()

    def _decode_bridge_events(
        self,
        payload: str | bytes,
    ) -> list[ChatRealtimeEvent]:
        envelope = json.loads(payload)

        if not isinstance(envelope, dict):
            raise ValueError(
                "Realtime envelope must be an object."
            )

        event_type = envelope.get("type")

        # Other bridge domains have their own consumers
        # and event contracts.
        if (
            not isinstance(event_type, str)
            or not event_type.startswith("call.")
        ):
            return []

        data = envelope.get("data")
        recipients = envelope.get("recipient_user_ids")

        if (
            not isinstance(data, dict)
            or not isinstance(recipients, list)
        ):
            raise ValueError(
                "Invalid call envelope data or recipients."
            )

        actor_id = uuid.UUID(
            str(envelope["actor_user_id"])
        )

        event_id = uuid.UUID(
            str(envelope["id"])
        )

        occurred_at = envelope["created_at"]

        if not occurred_at:
            raise ValueError(
                "Missing call event timestamp."
            )

        # Every call event must identify a valid call.
        uuid.UUID(str(data["call_id"]))

        recipient_ids = list(
            dict.fromkeys(
                uuid.UUID(str(item))
                for item in recipients
            )
        )

        if event_type == "call.signal":
            target = data.get("target_user_id")

            if target is not None:
                target_id = uuid.UUID(str(target))

                if recipient_ids != [target_id]:
                    raise ValueError(
                        "Signal recipients do not match its target."
                    )

            if actor_id in recipient_ids:
                raise ValueError(
                    "Call signals must not target their sender."
                )

        # Preserve the trusted backend publisher's explicit
        # recipient set. A targeted signal must never become
        # a conversation-wide event.
        return [
            ChatRealtimeEvent(
                event_id=event_id,
                event_type=event_type,
                occurred_at=occurred_at,
                actor_user_id=actor_id,
                target_user_id=recipient_id,
                data=dict(data),
            )
            for recipient_id in recipient_ids
        ]

    async def _dispatch_message(
        self,
        message: dict[str, Any],
    ) -> None:
        payload = message.get("data")

        if not isinstance(payload, (str, bytes)):
            return

        source_channel = message.get("channel")

        try:
            if isinstance(source_channel, bytes):
                source_channel = source_channel.decode("utf-8")

            if source_channel == self.channel:
                events = [
                    ChatRealtimeBus.decode(payload)
                ]

            elif source_channel == self.bridge_channel:
                events = self._decode_bridge_events(payload)

            else:
                return

        except Exception:
            logger.warning(
                "Discarding invalid realtime event on %s",
                source_channel,
            )
            return

        for event in events:
            if self._stopping.is_set():
                return

            try:
                async with self.session_factory() as session:
                    await self.dispatcher.dispatch(
                        session,
                        event=event,
                    )

            except asyncio.CancelledError:
                raise

            except Exception:
                # A failing event or recipient must not
                # terminate the subscriber worker.
                logger.exception(
                    "Realtime dispatch failed for event %s",
                    event.event_id,
                )

    async def _close_pubsub(
        self,
        pubsub: Any,
    ) -> None:
        try:
            await asyncio.wait_for(
                pubsub.unsubscribe(*self._channels),
                timeout=5.0,
            )

        except Exception:
            logger.debug(
                "Realtime unsubscribe failed",
                exc_info=True,
            )

        finally:
            try:
                await asyncio.wait_for(
                    pubsub.aclose(),
                    timeout=5.0,
                )

            except Exception:
                logger.debug(
                    "Realtime pubsub close failed",
                    exc_info=True,
                )

    async def _wait_before_retry(
        self,
        delay: float,
    ) -> None:
        try:
            await asyncio.wait_for(
                self._stopping.wait(),
                timeout=delay,
            )

        except asyncio.TimeoutError:
            pass

    async def run(self) -> None:
        retry_delay = 1.0

        while not self._stopping.is_set():
            pubsub = None

            try:
                pubsub = self.redis_client.pubsub()

                await pubsub.subscribe(
                    *self._channels
                )

                logger.info(
                    "Realtime subscriber listening on %s",
                    self._channels,
                )

                while not self._stopping.is_set():
                    message = await pubsub.get_message(
                        ignore_subscribe_messages=True,
                        timeout=1.0,
                    )

                    retry_delay = 1.0

                    if message is None:
                        await asyncio.sleep(0)
                        continue

                    if message.get("type") not in {
                        None,
                        "message",
                        "pmessage",
                    }:
                        continue

                    await self._dispatch_message(message)

            except asyncio.CancelledError:
                raise

            except (RedisError, OSError):
                if not self._stopping.is_set():
                    logger.warning(
                        "Realtime Redis connection lost; retrying",
                        exc_info=True,
                    )

            finally:
                if pubsub is not None:
                    await self._close_pubsub(pubsub)

            if not self._stopping.is_set():
                await self._wait_before_retry(
                    retry_delay
                )

                retry_delay = min(
                    retry_delay * 2.0,
                    30.0,
                )

        logger.info(
            "Realtime subscriber stopped"
        )


__all__ = [
    "ChatRealtimeSubscriber",
]