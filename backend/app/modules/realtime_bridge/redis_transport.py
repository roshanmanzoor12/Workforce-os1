from __future__ import annotations

import asyncio
import json
import os
from typing import Any

from redis.asyncio import Redis

from app.modules.chat.chat_redis import get_chat_redis_url


DEFAULT_REDIS_URL = "redis://127.0.0.1:6381/0"

DEFAULT_REALTIME_CHANNEL = "workforce:realtime:events"


class RealtimeRedisTransport:
    def __init__(
        self,
        *,
        redis_url: str | None = None,
        channel: str | None = None,
    ) -> None:
        self.redis_url = (
            (redis_url or "").strip()
            or get_chat_redis_url()
        )

        self.channel = (
            (channel or "").strip()
            or os.getenv(
                "WORKFORCE_REALTIME_CHANNEL",
                "",
            ).strip()
            or DEFAULT_REALTIME_CHANNEL
        )

        self._redis: Redis | None = None
        self._lock = asyncio.Lock()

    async def _start_locked(self) -> None:
        if self._redis is not None:
            return

        client = Redis.from_url(
            self.redis_url,
            encoding="utf-8",
            decode_responses=True,
            health_check_interval=30,
            socket_connect_timeout=5.0,
            socket_timeout=5.0,
        )

        try:
            if not await client.ping():
                raise RuntimeError(
                    "Realtime Redis health check failed."
                )

        except BaseException:
            try:
                await client.aclose()

            except Exception:
                pass

            raise

        self._redis = client

    async def start(self) -> None:
        async with self._lock:
            await self._start_locked()

    async def stop(self) -> None:
        async with self._lock:
            client = self._redis
            self._redis = None

            if client is not None:
                await client.aclose()

    async def publish(
        self,
        envelope: dict[str, Any],
    ) -> int:
        payload = json.dumps(
            envelope,
            separators=(",", ":"),
            default=str,
        )

        async with self._lock:
            await self._start_locked()

            assert self._redis is not None

            return int(
                await self._redis.publish(
                    self.channel,
                    payload,
                )
            )

    async def ping(self) -> bool:
        async with self._lock:
            await self._start_locked()

            assert self._redis is not None

            return bool(
                await self._redis.ping()
            )


_transport: RealtimeRedisTransport | None = None


def get_realtime_transport() -> RealtimeRedisTransport:
    global _transport

    if _transport is None:
        _transport = RealtimeRedisTransport()

    return _transport