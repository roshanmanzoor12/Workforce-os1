from __future__ import annotations

from typing import Any

from redis.asyncio import Redis
from redis.exceptions import RedisError as RedisClientError

from app.config import settings
from app.core.exceptions import RedisError
from app.core.logging import get_logger


logger = get_logger(__name__)


# =========================================================
# REDIS CLIENT
# =========================================================

redis_client: Redis = Redis.from_url(
    settings.redis_url,
    decode_responses=True,
    encoding="utf-8",
    health_check_interval=30,
    socket_connect_timeout=5,
    socket_timeout=5,
    retry_on_timeout=True,
)


# =========================================================
# KEY HELPERS
# =========================================================

def build_redis_key(*parts: str) -> str:
    """
    Build a namespaced Redis key.

    Example:
        build_redis_key("presence", "user", "123")

    Result:
        workforceos:presence:user:123
    """

    clean_parts = [
        str(part).strip(": ")
        for part in parts
        if str(part).strip(": ")
    ]

    suffix = ":".join(clean_parts)

    if suffix:
        return f"{settings.redis_key_prefix}{suffix}"

    return settings.redis_key_prefix.rstrip(":")


# =========================================================
# HEALTH CHECK
# =========================================================

async def check_redis() -> bool:
    """
    Check whether Redis is reachable.

    Returns:
        True  -> Redis is healthy
        False -> Redis is unavailable
    """

    try:
        result = await redis_client.ping()

        return bool(result)

    except Exception as exc:
        logger.error(
            "redis_health_check_failed",
            error=str(exc),
        )

        return False


async def test_redis_connection() -> None:
    """
    Raises RedisError if Redis is unavailable.

    Used during startup/readiness checks.
    """

    healthy = await check_redis()

    if not healthy:
        raise RedisError(
            "Unable to connect to WorkforceOS Redis."
        )


# =========================================================
# BASIC GET / SET
# =========================================================

async def redis_get(
    key: str,
) -> str | None:
    """
    Get a string value from Redis.
    """

    try:
        return await redis_client.get(
            build_redis_key(key)
        )

    except RedisClientError as exc:
        logger.exception(
            "redis_get_failed",
            key=key,
            error=str(exc),
        )

        raise RedisError(
            "Failed to read from Redis."
        ) from exc


async def redis_set(
    key: str,
    value: str | int | float,
    *,
    expire_seconds: int | None = None,
) -> bool:
    """
    Store a value in Redis.

    expire_seconds:
        Optional TTL in seconds.
    """

    try:
        result = await redis_client.set(
            build_redis_key(key),
            value,
            ex=expire_seconds,
        )

        return bool(result)

    except RedisClientError as exc:
        logger.exception(
            "redis_set_failed",
            key=key,
            error=str(exc),
        )

        raise RedisError(
            "Failed to write to Redis."
        ) from exc


async def redis_delete(
    key: str,
) -> int:
    """
    Delete one namespaced Redis key.

    Returns:
        Number of deleted keys.
    """

    try:
        return int(
            await redis_client.delete(
                build_redis_key(key)
            )
        )

    except RedisClientError as exc:
        logger.exception(
            "redis_delete_failed",
            key=key,
            error=str(exc),
        )

        raise RedisError(
            "Failed to delete Redis key."
        ) from exc


async def redis_exists(
    key: str,
) -> bool:
    """
    Check if a namespaced key exists.
    """

    try:
        result = await redis_client.exists(
            build_redis_key(key)
        )

        return bool(result)

    except RedisClientError as exc:
        logger.exception(
            "redis_exists_failed",
            key=key,
            error=str(exc),
        )

        raise RedisError(
            "Failed to check Redis key."
        ) from exc


# =========================================================
# TTL
# =========================================================

async def redis_expire(
    key: str,
    seconds: int,
) -> bool:
    """
    Set TTL for an existing Redis key.
    """

    if seconds <= 0:
        raise ValueError(
            "Redis expiration must be greater than 0 seconds."
        )

    try:
        result = await redis_client.expire(
            build_redis_key(key),
            seconds,
        )

        return bool(result)

    except RedisClientError as exc:
        logger.exception(
            "redis_expire_failed",
            key=key,
            error=str(exc),
        )

        raise RedisError(
            "Failed to set Redis expiration."
        ) from exc


async def redis_ttl(
    key: str,
) -> int:
    """
    Return TTL in seconds.

    Redis values:
        -1 = key exists but no expiry
        -2 = key does not exist
    """

    try:
        return int(
            await redis_client.ttl(
                build_redis_key(key)
            )
        )

    except RedisClientError as exc:
        logger.exception(
            "redis_ttl_failed",
            key=key,
            error=str(exc),
        )

        raise RedisError(
            "Failed to read Redis TTL."
        ) from exc


# =========================================================
# COUNTERS
# =========================================================

async def redis_increment(
    key: str,
    amount: int = 1,
    *,
    expire_seconds: int | None = None,
) -> int:
    """
    Increment an integer counter.

    Useful later for:
    - rate limiting
    - login attempts
    - OTP attempts
    - API usage
    """

    redis_key = build_redis_key(key)

    try:
        value = await redis_client.incrby(
            redis_key,
            amount,
        )

        if expire_seconds is not None:
            ttl = await redis_client.ttl(redis_key)

            if ttl == -1:
                await redis_client.expire(
                    redis_key,
                    expire_seconds,
                )

        return int(value)

    except RedisClientError as exc:
        logger.exception(
            "redis_increment_failed",
            key=key,
            error=str(exc),
        )

        raise RedisError(
            "Failed to increment Redis counter."
        ) from exc


# =========================================================
# HASH HELPERS
# =========================================================

async def redis_hash_set(
    key: str,
    mapping: dict[str, Any],
    *,
    expire_seconds: int | None = None,
) -> None:
    """
    Store a dictionary as a Redis hash.

    Useful later for:
    - presence
    - agent/device state
    - active sessions
    - live call state
    """

    redis_key = build_redis_key(key)

    serialized = {
        str(k): str(v)
        for k, v in mapping.items()
        if v is not None
    }

    try:
        if serialized:
            await redis_client.hset(
                redis_key,
                mapping=serialized,
            )

        if expire_seconds is not None:
            await redis_client.expire(
                redis_key,
                expire_seconds,
            )

    except RedisClientError as exc:
        logger.exception(
            "redis_hash_set_failed",
            key=key,
            error=str(exc),
        )

        raise RedisError(
            "Failed to write Redis hash."
        ) from exc


async def redis_hash_get_all(
    key: str,
) -> dict[str, str]:
    """
    Return an entire Redis hash.
    """

    try:
        result = await redis_client.hgetall(
            build_redis_key(key)
        )

        return dict(result)

    except RedisClientError as exc:
        logger.exception(
            "redis_hash_get_all_failed",
            key=key,
            error=str(exc),
        )

        raise RedisError(
            "Failed to read Redis hash."
        ) from exc


# =========================================================
# SET HELPERS
# =========================================================

async def redis_set_add(
    key: str,
    *values: str,
) -> int:
    """
    Add values to a Redis Set.

    Useful later for:
    - active users
    - connected devices
    - room participants
    """

    if not values:
        return 0

    try:
        return int(
            await redis_client.sadd(
                build_redis_key(key),
                *values,
            )
        )

    except RedisClientError as exc:
        logger.exception(
            "redis_set_add_failed",
            key=key,
            error=str(exc),
        )

        raise RedisError(
            "Failed to add values to Redis set."
        ) from exc


async def redis_set_remove(
    key: str,
    *values: str,
) -> int:
    """
    Remove values from a Redis Set.
    """

    if not values:
        return 0

    try:
        return int(
            await redis_client.srem(
                build_redis_key(key),
                *values,
            )
        )

    except RedisClientError as exc:
        logger.exception(
            "redis_set_remove_failed",
            key=key,
            error=str(exc),
        )

        raise RedisError(
            "Failed to remove values from Redis set."
        ) from exc


async def redis_set_members(
    key: str,
) -> set[str]:
    """
    Return all values from a Redis Set.
    """

    try:
        result = await redis_client.smembers(
            build_redis_key(key)
        )

        return set(result)

    except RedisClientError as exc:
        logger.exception(
            "redis_set_members_failed",
            key=key,
            error=str(exc),
        )

        raise RedisError(
            "Failed to read Redis set."
        ) from exc


# =========================================================
# PUB / SUB
# =========================================================

async def redis_publish(
    channel: str,
    message: str,
) -> int:
    """
    Publish a message to a namespaced Redis channel.

    Later used for:
    - websocket events
    - presence
    - notifications
    - chat fan-out
    """

    try:
        return int(
            await redis_client.publish(
                build_redis_key(
                    "channel",
                    channel,
                ),
                message,
            )
        )

    except RedisClientError as exc:
        logger.exception(
            "redis_publish_failed",
            channel=channel,
            error=str(exc),
        )

        raise RedisError(
            "Failed to publish Redis message."
        ) from exc


# =========================================================
# SERVER INFORMATION
# =========================================================

async def get_redis_info() -> dict[str, Any] | None:
    """
    Return limited Redis server information.

    Useful for platform-admin system health.
    """

    try:
        info = await redis_client.info(
            section="server"
        )

        return {
            "redis_version": info.get(
                "redis_version"
            ),
            "redis_mode": info.get(
                "redis_mode"
            ),
            "os": info.get("os"),
            "uptime_in_seconds": info.get(
                "uptime_in_seconds"
            ),
        }

    except Exception as exc:
        logger.warning(
            "redis_info_failed",
            error=str(exc),
        )

        return None


# =========================================================
# DEVELOPMENT / TEST CLEANUP
# =========================================================

async def delete_namespaced_keys(
    pattern: str = "*",
) -> int:
    """
    Delete WorkforceOS namespaced keys matching a pattern.

    IMPORTANT:
    Do not use Redis FLUSHDB because a Redis database may eventually
    be shared with other services.

    Example:
        delete_namespaced_keys("test:*")
    """

    redis_pattern = build_redis_key(
        pattern
    )

    deleted = 0

    try:
        async for key in redis_client.scan_iter(
            match=redis_pattern,
            count=100,
        ):
            deleted += int(
                await redis_client.delete(key)
            )

        return deleted

    except RedisClientError as exc:
        logger.exception(
            "redis_namespaced_cleanup_failed",
            pattern=pattern,
            error=str(exc),
        )

        raise RedisError(
            "Failed to clean Redis keys."
        ) from exc


# =========================================================
# SHUTDOWN
# =========================================================

async def close_redis() -> None:
    """
    Gracefully close Redis resources.

    Call this during FastAPI shutdown.
    """

    try:
        await redis_client.aclose()

        logger.info(
            "redis_connection_closed"
        )

    except Exception as exc:
        logger.warning(
            "redis_close_failed",
            error=str(exc),
        )