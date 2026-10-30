from __future__ import annotations

import time
import uuid
from typing import (
    Any,
    Protocol,
)


TYPING_TTL_SECONDS = 8

TYPING_KEY_PREFIX = (
    "workforceos:chat:typing:v1"
)


class RedisTypingProtocol(
    Protocol
):
    async def zadd(
        self,
        name: str,
        mapping: dict[
            str,
            float,
        ],
    ) -> Any:
        ...

    async def zrem(
        self,
        name: str,
        *values: str,
    ) -> Any:
        ...

    async def zremrangebyscore(
        self,
        name: str,
        min: float | str,
        max: float | str,
    ) -> Any:
        ...

    async def zrangebyscore(
        self,
        name: str,
        min: float | str,
        max: float | str,
    ) -> list[
        Any
    ]:
        ...

    async def expire(
        self,
        name: str,
        seconds: int,
    ) -> Any:
        ...


class TypingService:
    def __init__(
        self,
        redis_client: RedisTypingProtocol,
        *,
        ttl_seconds: int = TYPING_TTL_SECONDS,
    ) -> None:
        self.redis_client = redis_client

        self.ttl_seconds = max(
            2,
            min(
                int(
                    ttl_seconds
                ),
                30,
            ),
        )

    def _key(
        self,
        conversation_id: uuid.UUID,
    ) -> str:
        return (
            f"{TYPING_KEY_PREFIX}:"
            f"{conversation_id}"
        )

    async def start_typing(
        self,
        *,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        now = time.time()

        expires_at = (
            now
            + self.ttl_seconds
        )

        key = self._key(
            conversation_id
        )

        await self.redis_client.zadd(
            key,
            {
                str(
                    user_id
                ): expires_at,
            },
        )

        await self.redis_client.expire(
            key,
            self.ttl_seconds
            + 5,
        )

    async def stop_typing(
        self,
        *,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        await self.redis_client.zrem(
            self._key(
                conversation_id
            ),
            str(
                user_id
            ),
        )

    async def list_typing_users(
        self,
        *,
        conversation_id: uuid.UUID,
    ) -> list[
        uuid.UUID
    ]:
        now = time.time()

        key = self._key(
            conversation_id
        )

        await self.redis_client.zremrangebyscore(
            key,
            "-inf",
            now,
        )

        values = (
            await self.redis_client
            .zrangebyscore(
                key,
                now,
                "+inf",
            )
        )

        user_ids: list[
            uuid.UUID
        ] = []

        for value in values:
            if isinstance(
                value,
                bytes,
            ):
                value = value.decode(
                    "utf-8"
                )

            try:
                user_ids.append(
                    uuid.UUID(
                        str(
                            value
                        )
                    )
                )

            except ValueError:
                continue

        return user_ids


__all__ = [
    "TYPING_KEY_PREFIX",
    "TYPING_TTL_SECONDS",
    "RedisTypingProtocol",
    "TypingService",
]