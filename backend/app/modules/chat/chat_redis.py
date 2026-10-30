from __future__ import annotations

import os
from typing import Any

from redis.asyncio import Redis

from app.config import settings


DEFAULT_CHAT_REDIS_URL = "redis://127.0.0.1:6381/0"

_chat_redis_client: Redis | None = None


def get_chat_redis_url() -> str:
    environment_url = os.getenv(
        "REDIS_URL",
        "",
    ).strip()

    configured_url = str(
        getattr(
            settings,
            "redis_url",
            "",
        )
        or ""
    ).strip()

    return (
        environment_url
        or configured_url
        or DEFAULT_CHAT_REDIS_URL
    )


def get_chat_redis() -> Redis:
    global _chat_redis_client

    if _chat_redis_client is None:
        _chat_redis_client = Redis.from_url(
            get_chat_redis_url(),
            encoding="utf-8",
            decode_responses=True,
            health_check_interval=30,
            socket_connect_timeout=5.0,
            socket_timeout=5.0,
        )

    return _chat_redis_client


async def close_chat_redis() -> None:
    global _chat_redis_client

    client = _chat_redis_client
    _chat_redis_client = None

    if client is not None:
        await client.aclose()


async def ping_chat_redis() -> bool:
    result: Any = await get_chat_redis().ping()

    return bool(result)


__all__ = [
    "DEFAULT_CHAT_REDIS_URL",
    "close_chat_redis",
    "get_chat_redis",
    "get_chat_redis_url",
    "ping_chat_redis",
]