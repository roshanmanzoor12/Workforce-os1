from __future__ import annotations

import pytest

from app.modules.channels.realtime_pubsub import (
    ChannelRealtimePubSubSession,
)


class FakePubSub:
    def __init__(
        self,
    ) -> None:
        self.subscribed: list[str] = []
        self.unsubscribed: list[str] = []

        self.closed = False

        self.messages: list[dict] = []

    async def subscribe(
        self,
        channel: str,
    ) -> None:
        self.subscribed.append(
            channel
        )

    async def unsubscribe(
        self,
        channel: str,
    ) -> None:
        self.unsubscribed.append(
            channel
        )

    async def aclose(
        self,
    ) -> None:
        self.closed = True

    async def get_message(
        self,
        **kwargs,
    ):
        if not self.messages:
            return None

        return self.messages.pop(
            0
        )


class FakeRedis:
    def __init__(
        self,
    ) -> None:
        self.pubsub_instance = (
            FakePubSub()
        )

    def pubsub(
        self,
    ) -> FakePubSub:
        return self.pubsub_instance


@pytest.mark.asyncio
async def test_pubsub_open_subscribes() -> None:
    redis = FakeRedis()

    session = (
        ChannelRealtimePubSubSession(
            redis=redis,
            channel="abc",
        )
    )

    await session.open()

    assert (
        redis.pubsub_instance.subscribed
        == ["abc"]
    )


@pytest.mark.asyncio
async def test_pubsub_close_unsubscribes_and_closes() -> None:
    redis = FakeRedis()

    session = (
        ChannelRealtimePubSubSession(
            redis=redis,
            channel="abc",
        )
    )

    await session.open()
    await session.close()

    assert (
        redis.pubsub_instance.unsubscribed
        == ["abc"]
    )

    assert (
        redis.pubsub_instance.closed
        is True
    )


@pytest.mark.asyncio
async def test_pubsub_close_is_idempotent() -> None:
    redis = FakeRedis()

    session = (
        ChannelRealtimePubSubSession(
            redis=redis,
            channel="abc",
        )
    )

    await session.open()

    await session.close()
    await session.close()

    assert (
        redis.pubsub_instance.unsubscribed
        == ["abc"]
    )


@pytest.mark.asyncio
async def test_pubsub_decodes_bytes() -> None:
    redis = FakeRedis()

    redis.pubsub_instance.messages.append(
        {
            "data":
                b'{"hello":"world"}'
        }
    )

    session = (
        ChannelRealtimePubSubSession(
            redis=redis,
            channel="abc",
        )
    )

    await session.open()

    payload = await (
        session.next_payload()
    )

    assert (
        payload
        == '{"hello":"world"}'
    )


@pytest.mark.asyncio
async def test_pubsub_returns_none_without_message() -> None:
    redis = FakeRedis()

    session = (
        ChannelRealtimePubSubSession(
            redis=redis,
            channel="abc",
        )
    )

    await session.open()

    assert (
        await session.next_payload()
        is None
    )