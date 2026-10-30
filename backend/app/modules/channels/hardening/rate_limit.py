from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any


_FIXED_WINDOW_LUA = """
local current = redis.call("INCR", KEYS[1])

if current == 1 then
    redis.call("EXPIRE", KEYS[1], ARGV[1])
end

local ttl = redis.call("TTL", KEYS[1])

return {current, ttl}
"""


@dataclass(
    frozen=True,
    slots=True,
)
class ChannelRateLimitDecision:
    allowed: bool

    limit: int
    used: int
    remaining: int

    retry_after_seconds: int

    bucket: str


class ChannelRateLimiter:
    """
    Redis-backed fixed-window limiter for websocket/realtime actions.

    This is intentionally kept independent of FastAPI so the same limiter
    can be used by HTTP ticket creation and websocket event handling.
    """

    def __init__(
        self,
        redis: Any,
        *,
        prefix: str = (
            "workforce:"
            "channel-realtime:"
            "rate:"
        ),
    ) -> None:
        self.redis = redis
        self.prefix = prefix

    @staticmethod
    def _safe_part(
        value: object,
    ) -> str:
        text = str(
            value
        ).strip()

        if not text:
            return "_"

        return (
            text
            .replace(
                ":",
                "_",
            )
            .replace(
                " ",
                "_",
            )
        )

    def build_key(
        self,
        *,
        bucket: str,
        workspace_id: object,
        channel_id: object | None = None,
        user_id: object | None = None,
    ) -> str:
        parts = [
            self.prefix.rstrip(
                ":"
            ),
            self._safe_part(
                bucket
            ),
            self._safe_part(
                workspace_id
            ),
        ]

        if channel_id is not None:
            parts.append(
                self._safe_part(
                    channel_id
                )
            )

        if user_id is not None:
            parts.append(
                self._safe_part(
                    user_id
                )
            )

        return ":".join(
            parts
        )

    async def check(
        self,
        *,
        bucket: str,
        workspace_id: object,
        channel_id: object | None = None,
        user_id: object | None = None,
        limit: int,
        window_seconds: int,
    ) -> ChannelRateLimitDecision:
        if limit <= 0:
            raise ValueError(
                "Rate limit must be positive."
            )

        if window_seconds <= 0:
            raise ValueError(
                "Rate-limit window must be positive."
            )

        key = self.build_key(
            bucket=bucket,
            workspace_id=workspace_id,
            channel_id=channel_id,
            user_id=user_id,
        )

        result = await self.redis.eval(
            _FIXED_WINDOW_LUA,
            1,
            key,
            window_seconds,
        )

        used = int(
            result[0]
        )

        ttl = int(
            result[1]
        )

        if ttl < 0:
            ttl = window_seconds

        allowed = (
            used <= limit
        )

        remaining = max(
            limit - used,
            0,
        )

        return ChannelRateLimitDecision(
            allowed=allowed,
            limit=limit,
            used=used,
            remaining=remaining,
            retry_after_seconds=(
                0
                if allowed
                else max(
                    ttl,
                    1,
                )
            ),
            bucket=bucket,
        )

    async def clear(
        self,
        *,
        bucket: str,
        workspace_id: object,
        channel_id: object | None = None,
        user_id: object | None = None,
    ) -> None:
        key = self.build_key(
            bucket=bucket,
            workspace_id=workspace_id,
            channel_id=channel_id,
            user_id=user_id,
        )

        await self.redis.delete(
            key
        )


def unix_seconds() -> int:
    return int(
        time.time()
    )