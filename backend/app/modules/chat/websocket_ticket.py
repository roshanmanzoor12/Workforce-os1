from __future__ import annotations

import secrets
import uuid
from typing import (
    Any,
    Protocol,
)


WEBSOCKET_TICKET_PREFIX = (
    "workforceos:chat:ws-ticket:v1"
)

DEFAULT_TICKET_TTL_SECONDS = 60


class WebSocketTicketRedisProtocol(
    Protocol
):
    async def set(
        self,
        name: str,
        value: str,
        *,
        ex: int,
        nx: bool,
    ) -> Any:
        ...

    async def getdel(
        self,
        name: str,
    ) -> Any:
        ...


class WebSocketTicketService:
    def __init__(
        self,
        redis_client: WebSocketTicketRedisProtocol,
        *,
        ttl_seconds: int = DEFAULT_TICKET_TTL_SECONDS,
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
        token: str,
    ) -> str:
        return (
            f"{WEBSOCKET_TICKET_PREFIX}:"
            f"{token}"
        )

    async def issue(
        self,
        *,
        user_id: uuid.UUID,
    ) -> str:
        for _ in range(
            5
        ):
            token = secrets.token_urlsafe(
                32
            )

            result = await self.redis_client.set(
                self._key(
                    token
                ),
                str(
                    user_id
                ),
                ex=self.ttl_seconds,
                nx=True,
            )

            if result:
                return token

        raise RuntimeError(
            "Unable to issue WebSocket ticket."
        )

    async def consume(
        self,
        *,
        token: str,
    ) -> uuid.UUID | None:
        normalized = token.strip()

        if not normalized:
            return None

        value = await self.redis_client.getdel(
            self._key(
                normalized
            )
        )

        if value is None:
            return None

        if isinstance(
            value,
            bytes,
        ):
            value = value.decode(
                "utf-8"
            )

        try:
            return uuid.UUID(
                str(
                    value
                )
            )

        except ValueError:
            return None


__all__ = [
    "DEFAULT_TICKET_TTL_SECONDS",
    "WEBSOCKET_TICKET_PREFIX",
    "WebSocketTicketRedisProtocol",
    "WebSocketTicketService",
]