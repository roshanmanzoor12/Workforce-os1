from __future__ import annotations

import asyncio
import math
import uuid
from collections import defaultdict

from fastapi import WebSocket

from .realtime_events import ChatRealtimeEvent


class ChatConnectionManager:
    def __init__(
        self,
        *,
        send_timeout_seconds: float = 10.0,
    ) -> None:
        if (
            not math.isfinite(send_timeout_seconds)
            or send_timeout_seconds <= 0
        ):
            raise ValueError(
                "send_timeout_seconds must be positive and finite."
            )

        self._connections: dict[
            uuid.UUID,
            set[WebSocket],
        ] = defaultdict(set)

        self._send_locks: dict[
            WebSocket,
            asyncio.Lock,
        ] = {}

        self._lock = asyncio.Lock()
        self._send_timeout_seconds = send_timeout_seconds

    async def connect(
        self,
        *,
        user_id: uuid.UUID,
        websocket: WebSocket,
        accept: bool = True,
    ) -> None:
        if accept:
            await websocket.accept()

        async with self._lock:
            self._connections[user_id].add(websocket)

            self._send_locks.setdefault(
                websocket,
                asyncio.Lock(),
            )

    async def disconnect(
        self,
        *,
        user_id: uuid.UUID,
        websocket: WebSocket,
    ) -> None:
        async with self._lock:
            connections = self._connections.get(user_id)

            if not connections:
                return

            connections.discard(websocket)
            self._send_locks.pop(websocket, None)

            if not connections:
                self._connections.pop(user_id, None)

    async def _send_one(
        self,
        *,
        user_id: uuid.UUID,
        websocket: WebSocket,
        send_lock: asyncio.Lock,
        payload: str,
    ) -> int:
        async def send() -> None:
            async with send_lock:
                await websocket.send_text(payload)

        try:
            await asyncio.wait_for(
                send(),
                timeout=self._send_timeout_seconds,
            )

            return 1

        except asyncio.CancelledError:
            raise

        except Exception:
            await self.disconnect(
                user_id=user_id,
                websocket=websocket,
            )

            try:
                await asyncio.wait_for(
                    websocket.close(code=1011),
                    timeout=2.0,
                )

            except Exception:
                pass

            return 0

    async def send_to_user(
        self,
        *,
        user_id: uuid.UUID,
        event: ChatRealtimeEvent,
    ) -> int:
        async with self._lock:
            connections = [
                (
                    websocket,
                    self._send_locks[websocket],
                )
                for websocket in self._connections.get(
                    user_id,
                    set(),
                )
            ]

        if not connections:
            return 0

        payload = event.to_json()

        results = await asyncio.gather(
            *[
                self._send_one(
                    user_id=user_id,
                    websocket=websocket,
                    send_lock=send_lock,
                    payload=payload,
                )
                for websocket, send_lock in connections
            ]
        )

        return sum(results)

    async def connection_count(
        self,
        *,
        user_id: uuid.UUID,
    ) -> int:
        async with self._lock:
            return len(
                self._connections.get(
                    user_id,
                    set(),
                )
            )

    async def is_connected(
        self,
        *,
        user_id: uuid.UUID,
    ) -> bool:
        return (
            await self.connection_count(
                user_id=user_id,
            )
            > 0
        )


chat_connection_manager = ChatConnectionManager()


__all__ = [
    "ChatConnectionManager",
    "chat_connection_manager",
]