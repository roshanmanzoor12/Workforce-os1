from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


_ATOMIC_GETDEL_LUA = """
local value = redis.call("GET", KEYS[1])

if value then
    redis.call("DEL", KEYS[1])
end

return value
"""


@dataclass(
    frozen=True,
    slots=True,
)
class TicketConsumeResult:
    found: bool
    payload: dict[str, Any] | None
    raw_value: str | None


class AtomicRealtimeTicketStore:
    """
    Atomic one-use realtime ticket consumer.

    Redis GET followed by DELETE has a race when two websocket
    connections try to consume the same ticket concurrently.

    This class prefers Redis GETDEL and falls back to a small Lua script,
    preserving atomic one-use semantics on older Redis clients/servers.
    """

    def __init__(
        self,
        redis: Any,
        *,
        key_prefix: str = (
            "workforce:"
            "channel-realtime:"
            "ticket:"
        ),
    ) -> None:
        self.redis = redis

        self.key_prefix = (
            key_prefix
        )

    def build_key(
        self,
        ticket: str,
    ) -> str:
        normalized = ticket.strip()

        if not normalized:
            raise ValueError(
                "Realtime ticket cannot be empty."
            )

        return (
            f"{self.key_prefix}"
            f"{normalized}"
        )

    async def store(
        self,
        *,
        ticket: str,
        payload: dict[str, Any],
        ttl_seconds: int,
    ) -> None:
        if ttl_seconds <= 0:
            raise ValueError(
                "Ticket TTL must be positive."
            )

        key = self.build_key(
            ticket
        )

        serialized = json.dumps(
            payload,
            separators=(
                ",",
                ":",
            ),
            sort_keys=True,
            default=str,
        )

        await self.redis.set(
            key,
            serialized,
            ex=ttl_seconds,
        )

    async def _getdel(
        self,
        key: str,
    ) -> Any:
        getdel = getattr(
            self.redis,
            "getdel",
            None,
        )

        if callable(
            getdel
        ):
            return await getdel(
                key
            )

        return await self.redis.eval(
            _ATOMIC_GETDEL_LUA,
            1,
            key,
        )

    @staticmethod
    def _decode(
        raw: Any,
    ) -> str | None:
        if raw is None:
            return None

        if isinstance(
            raw,
            bytes,
        ):
            return raw.decode(
                "utf-8"
            )

        if isinstance(
            raw,
            str,
        ):
            return raw

        return str(
            raw
        )

    async def consume(
        self,
        ticket: str,
    ) -> TicketConsumeResult:
        key = self.build_key(
            ticket
        )

        raw = await self._getdel(
            key
        )

        decoded = self._decode(
            raw
        )

        if decoded is None:
            return TicketConsumeResult(
                found=False,
                payload=None,
                raw_value=None,
            )

        try:
            payload = json.loads(
                decoded
            )
        except json.JSONDecodeError:
            return TicketConsumeResult(
                found=True,
                payload=None,
                raw_value=decoded,
            )

        if not isinstance(
            payload,
            dict,
        ):
            return TicketConsumeResult(
                found=True,
                payload=None,
                raw_value=decoded,
            )

        return TicketConsumeResult(
            found=True,
            payload=payload,
            raw_value=decoded,
        )

    async def revoke(
        self,
        ticket: str,
    ) -> bool:
        key = self.build_key(
            ticket
        )

        deleted = await self.redis.delete(
            key
        )

        return bool(
            deleted
        )