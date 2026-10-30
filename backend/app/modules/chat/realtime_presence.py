from __future__ import annotations

import time
import uuid
from typing import (
    Any,
    Protocol,
)


REALTIME_PRESENCE_PREFIX = (
    "workforceos:chat:presence:v1"
)

DEFAULT_PRESENCE_TTL_SECONDS = 45


class RealtimePresenceRedisProtocol(
    Protocol
):
    async def set(
        self,
        name: str,
        value: str,
        *,
        ex: int,
    ) -> Any:
        ...

    async def get(
        self,
        name: str,
    ) -> Any:
        ...

    async def delete(
        self,
        *names: str,
    ) -> Any:
        ...


class RealtimePresenceTracker:
    def __init__(
        self,
        redis_client: RealtimePresenceRedisProtocol,
        *,
        ttl_seconds: int = (
            DEFAULT_PRESENCE_TTL_SECONDS
        ),
    ) -> None:
        self.redis_client = redis_client

        self.ttl_seconds = max(
            15,
            min(
                int(
                    ttl_seconds
                ),
                300,
            ),
        )

    @staticmethod
    def _key(
        user_id: uuid.UUID,
    ) -> str:
        return (
            f"{REALTIME_PRESENCE_PREFIX}:"
            f"{user_id}"
        )

    async def heartbeat(
        self,
        *,
        user_id: uuid.UUID,
    ) -> int:
        now = int(
            time.time()
        )

        await self.redis_client.set(
            self._key(
                user_id
            ),
            str(
                now
            ),
            ex=self.ttl_seconds,
        )

        return now

    async def mark_offline(
        self,
        *,
        user_id: uuid.UUID,
    ) -> None:
        await self.redis_client.delete(
            self._key(
                user_id
            )
        )

    async def is_online(
        self,
        *,
        user_id: uuid.UUID,
    ) -> bool:
        value = await self.redis_client.get(
            self._key(
                user_id
            )
        )

        return value is not None


__all__ = [
    "DEFAULT_PRESENCE_TTL_SECONDS",
    "REALTIME_PRESENCE_PREFIX",
    "RealtimePresenceRedisProtocol",
    "RealtimePresenceTracker",
]