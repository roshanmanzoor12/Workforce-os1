from __future__ import annotations

import asyncio
import json
import uuid

import pytest
from redis.asyncio import Redis

from app.modules.realtime_bridge.envelope import (
    build_realtime_envelope,
)
from app.modules.realtime_bridge.redis_transport import (
    DEFAULT_REALTIME_CHANNEL,
    get_realtime_transport,
)


@pytest.mark.asyncio
async def test_live_redis_publish_receive(
) -> None:
    subscriber = Redis.from_url(
        "redis://127.0.0.1:6381/0",
        encoding="utf-8",
        decode_responses=True,
    )

    pubsub = subscriber.pubsub()

    await pubsub.subscribe(
        DEFAULT_REALTIME_CHANNEL
    )

    try:
        await asyncio.sleep(
            0.1
        )

        event_id = uuid.uuid4()

        envelope = build_realtime_envelope(
            event_type=(
                "phase11.6.live-test"
            ),
            actor_user_id=uuid.uuid4(),
            recipient_user_ids=[
                uuid.uuid4()
            ],
            data={
                "event_id": str(
                    event_id
                )
            },
        )

        transport = (
            get_realtime_transport()
        )

        await transport.start()

        await transport.publish(
            envelope
        )

        received = None

        for _ in range(30):
            message = (
                await pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=0.2,
                )
            )

            if message is None:
                await asyncio.sleep(
                    0.05
                )
                continue

            received = json.loads(
                message["data"]
            )

            break

        assert received is not None

        assert (
            received["type"]
            == "phase11.6.live-test"
        )

        assert (
            received["data"][
                "event_id"
            ]
            == str(event_id)
        )

    finally:
        await pubsub.unsubscribe(
            DEFAULT_REALTIME_CHANNEL
        )

        await pubsub.aclose()

        await subscriber.aclose()