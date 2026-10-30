from __future__ import annotations

import json
from contextlib import suppress
from typing import Any


class ChannelRealtimePubSubSession:
    """
    Owns one Redis pubsub subscription lifecycle.

    Calling close() is idempotent.

    It guarantees best-effort unsubscribe and aclose on every
    WebSocket exit path.
    """

    def __init__(
        self,
        *,
        redis: Any,
        channel: str,
    ) -> None:
        self.redis = redis
        self.channel = channel

        self.pubsub = None
        self.opened = False
        self.closed = False

    async def open(
        self,
    ) -> None:
        if self.opened:
            return

        if self.closed:
            raise RuntimeError(
                "Closed pubsub session "
                "cannot be reopened."
            )

        pubsub = self.redis.pubsub()

        try:
            await pubsub.subscribe(
                self.channel
            )

        except Exception:
            with suppress(
                Exception
            ):
                await pubsub.aclose()

            raise

        self.pubsub = pubsub
        self.opened = True

    async def next_payload(
        self,
        *,
        timeout: float = 1.0,
    ) -> str | None:
        if (
            not self.opened
            or self.pubsub is None
        ):
            raise RuntimeError(
                "Pubsub session is not open."
            )

        message = await (
            self.pubsub.get_message(
                ignore_subscribe_messages=True,
                timeout=timeout,
            )
        )

        if message is None:
            return None

        data = message.get(
            "data"
        )

        if data is None:
            return None

        if isinstance(
            data,
            bytes,
        ):
            return data.decode(
                "utf-8",
                errors="replace",
            )

        if isinstance(
            data,
            str,
        ):
            return data

        return json.dumps(
            data,
            default=str,
            separators=(
                ",",
                ":",
            ),
        )

    async def close(
        self,
    ) -> None:
        if self.closed:
            return

        self.closed = True

        pubsub = self.pubsub

        self.pubsub = None
        self.opened = False

        if pubsub is None:
            return

        with suppress(
            Exception
        ):
            await pubsub.unsubscribe(
                self.channel
            )

        with suppress(
            Exception
        ):
            await pubsub.aclose()

    async def __aenter__(
        self,
    ) -> "ChannelRealtimePubSubSession":
        await self.open()

        return self

    async def __aexit__(
        self,
        exc_type,
        exc,
        traceback,
    ) -> None:
        await self.close()


__all__ = [
    "ChannelRealtimePubSubSession",
]