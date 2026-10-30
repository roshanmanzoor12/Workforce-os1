from __future__ import annotations

from collections.abc import (
    Awaitable,
    Callable,
)
from typing import Protocol

from app.modules.notifications.schemas import (
    NotificationRealtimeEvent,
)


class NotificationRealtimePublisher(
    Protocol
):
    async def publish(
        self,
        event: NotificationRealtimeEvent,
    ) -> None:
        ...


class NoopNotificationRealtimePublisher:
    async def publish(
        self,
        event: NotificationRealtimeEvent,
    ) -> None:
        # Persistence remains authoritative.
        #
        # A transport adapter can replace this publisher
        # without changing notification business logic.
        return None


class CallbackNotificationRealtimePublisher:
    def __init__(
        self,
        callback: Callable[
            [
                NotificationRealtimeEvent
            ],
            Awaitable[None],
        ],
    ) -> None:
        self.callback = callback

    async def publish(
        self,
        event: NotificationRealtimeEvent,
    ) -> None:
        await self.callback(
            event
        )


_default_publisher: (
    NotificationRealtimePublisher
) = NoopNotificationRealtimePublisher()


def get_notification_realtime_publisher(
) -> NotificationRealtimePublisher:
    return _default_publisher


def set_notification_realtime_publisher(
    publisher: (
        NotificationRealtimePublisher
    ),
) -> None:
    global _default_publisher

    _default_publisher = publisher


__all__ = [
    "NotificationRealtimePublisher",
    "NoopNotificationRealtimePublisher",
    "CallbackNotificationRealtimePublisher",
    "get_notification_realtime_publisher",
    "set_notification_realtime_publisher",
]