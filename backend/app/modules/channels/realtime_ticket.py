from __future__ import annotations

import json
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from app.core.redis import redis_client
from app.modules.channels.hardening import (
    channel_realtime_metrics,
    get_channel_hardening_settings,
)


_ATOMIC_CONSUME_LUA = """
local value = redis.call("GET", KEYS[1])

if not value then
    return nil
end

redis.call("DEL", KEYS[1])

return value
"""


@dataclass(
    frozen=True,
    slots=True,
)
class WorkspaceChannelRealtimeIdentity:
    workspace_id: uuid.UUID
    channel_id: uuid.UUID
    user_id: uuid.UUID


class WorkspaceChannelRealtimeTicketService:
    """
    Production one-use realtime ticket service.

    Security contract:

    JWT
      -> authenticated HTTP ticket endpoint
      -> short-lived opaque Redis ticket
      -> WebSocket ?ticket=...
      -> atomic consume

    A ticket can be consumed successfully at most once.
    """

    PREFIX = (
        "workforce:channels:"
        "realtime-ticket"
    )

    @classmethod
    def key(
        cls,
        ticket: str,
    ) -> str:
        return (
            f"{cls.PREFIX}:"
            f"{ticket}"
        )

    @staticmethod
    def _decode_raw(
        raw: Any,
    ) -> str | None:
        if raw is None:
            return None

        if isinstance(
            raw,
            bytes,
        ):
            return raw.decode(
                "utf-8",
                errors="strict",
            )

        if isinstance(
            raw,
            str,
        ):
            return raw

        return str(raw)

    async def create(
        self,
        *,
        workspace_id: uuid.UUID,
        channel_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> tuple[
        str,
        int,
    ]:
        settings = (
            get_channel_hardening_settings()
        )

        ttl_seconds = (
            settings.ticket_ttl_seconds
        )

        ticket = secrets.token_urlsafe(
            48
        )

        value = json.dumps(
            {
                "workspace_id": str(
                    workspace_id
                ),
                "channel_id": str(
                    channel_id
                ),
                "user_id": str(
                    user_id
                ),
                "created_at": (
                    datetime.now(
                        timezone.utc
                    ).isoformat()
                ),
            },
            separators=(
                ",",
                ":",
            ),
        )

        await redis_client.set(
            self.key(
                ticket
            ),
            value,
            ex=ttl_seconds,
        )

        channel_realtime_metrics.increment(
            "ticket.created"
        )

        return (
            ticket,
            ttl_seconds,
        )

    async def consume(
        self,
        *,
        ticket: str,
    ) -> (
        WorkspaceChannelRealtimeIdentity
        | None
    ):
        normalized = (
            str(ticket or "")
            .strip()
        )

        if not normalized:
            channel_realtime_metrics.increment(
                "ticket.invalid"
            )

            return None

        key = self.key(
            normalized
        )

        raw = await redis_client.eval(
            _ATOMIC_CONSUME_LUA,
            1,
            key,
        )

        raw_text = self._decode_raw(
            raw
        )

        if raw_text is None:
            channel_realtime_metrics.increment(
                "ticket.missing_or_consumed"
            )

            return None

        try:
            data = json.loads(
                raw_text
            )

            identity = (
                WorkspaceChannelRealtimeIdentity(
                    workspace_id=uuid.UUID(
                        str(
                            data[
                                "workspace_id"
                            ]
                        )
                    ),
                    channel_id=uuid.UUID(
                        str(
                            data[
                                "channel_id"
                            ]
                        )
                    ),
                    user_id=uuid.UUID(
                        str(
                            data[
                                "user_id"
                            ]
                        )
                    ),
                )
            )

        except (
            KeyError,
            TypeError,
            ValueError,
            json.JSONDecodeError,
        ):
            channel_realtime_metrics.increment(
                "ticket.invalid_payload"
            )

            return None

        channel_realtime_metrics.increment(
            "ticket.consumed"
        )

        channel_realtime_metrics.log_event(
            event="ticket_consumed",
            workspace_id=(
                identity.workspace_id
            ),
            channel_id=(
                identity.channel_id
            ),
            user_id=identity.user_id,
        )

        return identity


channel_realtime_ticket_service = (
    WorkspaceChannelRealtimeTicketService()
)


__all__ = [
    "WorkspaceChannelRealtimeIdentity",
    "WorkspaceChannelRealtimeTicketService",
    "channel_realtime_ticket_service",
]