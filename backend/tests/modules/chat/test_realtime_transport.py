from __future__ import annotations

import uuid

import pytest
from fastapi.routing import (
    APIRoute,
    APIWebSocketRoute,
)

from app.modules.chat.realtime_events import (
    ChatRealtimeEvent,
)
from app.modules.chat.realtime_enums import (
    ChatRealtimeEventType,
)
from app.modules.chat.realtime_router import (
    router,
)
from app.modules.chat.websocket_ticket import (
    WebSocketTicketService,
)


class FakeTicketRedis:
    def __init__(
        self,
    ):
        self.values = {}

    async def set(
        self,
        name,
        value,
        *,
        ex,
        nx,
    ):
        if (
            nx
            and name in self.values
        ):
            return False

        self.values[
            name
        ] = value

        return True

    async def getdel(
        self,
        name,
    ):
        return self.values.pop(
            name,
            None,
        )


@pytest.mark.asyncio
async def test_websocket_ticket_is_one_time():
    redis_client = FakeTicketRedis()

    service = WebSocketTicketService(
        redis_client
    )

    user_id = uuid.uuid4()

    ticket = await service.issue(
        user_id=user_id
    )

    first = await service.consume(
        token=ticket
    )

    second = await service.consume(
        token=ticket
    )

    assert first == user_id
    assert second is None


@pytest.mark.asyncio
async def test_blank_ticket_is_rejected():
    service = WebSocketTicketService(
        FakeTicketRedis()
    )

    result = await service.consume(
        token="   "
    )

    assert result is None


def test_realtime_router_contract():
    http_contract = set()

    websocket_contract = set()

    for route in router.routes:
        if isinstance(
            route,
            APIRoute,
        ):
            for method in route.methods:
                http_contract.add(
                    (
                        method,
                        route.path,
                    )
                )

        if isinstance(
            route,
            APIWebSocketRoute,
        ):
            websocket_contract.add(
                route.path
            )

    assert (
        "POST",
        "/chat/realtime/ticket",
    ) in http_contract

    assert (
        "/chat/realtime/ws"
        in websocket_contract
    )


def test_realtime_event_supports_target():
    user_id = uuid.uuid4()

    event = ChatRealtimeEvent(
        event_type=(
            ChatRealtimeEventType
            .PRESENCE_UPDATED
        ),
        target_user_id=user_id,
    )

    assert (
        event.target_user_id
        == user_id
    )