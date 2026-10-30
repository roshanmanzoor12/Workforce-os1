from __future__ import annotations

import ast
from pathlib import Path

import pytest

from app.modules.channels.realtime_pubsub import (
    ChannelRealtimePubSubSession,
)
from app.modules.channels.realtime_replay import (
    ChannelRealtimeReplayPolicy,
    ReplayWindowExceeded,
)


BACKEND_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)


class FakePubSub:
    def __init__(
        self,
    ) -> None:
        self.subscribed = []
        self.unsubscribed = []
        self.closed = False

    async def subscribe(
        self,
        channel,
    ):
        self.subscribed.append(
            channel
        )

    async def unsubscribe(
        self,
        channel,
    ):
        self.unsubscribed.append(
            channel
        )

    async def aclose(
        self,
    ):
        self.closed = True

    async def get_message(
        self,
        **kwargs,
    ):
        return {
            "data": b'{"ok":true}'
        }


class FakeRedis:
    def __init__(
        self,
    ) -> None:
        self.instance = FakePubSub()

    def pubsub(
        self,
    ):
        return self.instance


def test_replay_accepts_bounded_window():
    policy = (
        ChannelRealtimeReplayPolicy(
            batch_size=200,
            max_events=1000,
        )
    )

    limit = policy.validate(
        after_sequence=100,
        current_sequence=300,
        requested_limit=500,
    )

    assert limit == 200


def test_replay_rejects_old_cursor():
    policy = (
        ChannelRealtimeReplayPolicy(
            batch_size=200,
            max_events=1000,
        )
    )

    with pytest.raises(
        ReplayWindowExceeded
    ):
        policy.validate(
            after_sequence=1,
            current_sequence=2000,
            requested_limit=100,
        )


def test_replay_rejects_future_cursor():
    policy = (
        ChannelRealtimeReplayPolicy(
            batch_size=200,
            max_events=1000,
        )
    )

    with pytest.raises(
        ReplayWindowExceeded
    ):
        policy.validate(
            after_sequence=101,
            current_sequence=100,
            requested_limit=50,
        )


@pytest.mark.asyncio
async def test_pubsub_lifecycle_cleanup():
    redis = FakeRedis()

    session = (
        ChannelRealtimePubSubSession(
            redis=redis,
            channel="test-channel",
        )
    )

    await session.open()

    assert (
        redis.instance.subscribed
        == ["test-channel"]
    )

    payload = await (
        session.next_payload()
    )

    assert payload == '{"ok":true}'

    await session.close()
    await session.close()

    assert (
        redis.instance.unsubscribed
        == ["test-channel"]
    )

    assert redis.instance.closed


def test_attachment_membership_uses_left_at():
    path = (
        BACKEND_ROOT
        / "app"
        / "modules"
        / "attachments"
        / "service.py"
    )

    tree = ast.parse(
        path.read_text(
            encoding="utf-8"
        )
    )

    bad = []

    left_at = False

    for node in ast.walk(
        tree
    ):
        if not isinstance(
            node,
            ast.Attribute,
        ):
            continue

        if (
            node.attr == "is_active"
            and isinstance(
                node.value,
                ast.Name,
            )
            and node.value.id
            == "WorkspaceChannelMember"
        ):
            bad.append(
                node.lineno
            )

        if (
            node.attr == "left_at"
            and isinstance(
                node.value,
                ast.Name,
            )
            and node.value.id
            == "WorkspaceChannelMember"
        ):
            left_at = True

    assert bad == []
    assert left_at


def test_read_state_repository_wires_upsert():
    path = (
        BACKEND_ROOT
        / "app"
        / "modules"
        / "channels"
        / "read_state_repository.py"
    )

    source = path.read_text(
        encoding="utf-8"
    )

    assert (
        "ChannelReadStateUpserter"
        in source
    )

    assert (
        ".upsert_and_flush("
        in source
    )


def test_ticket_consume_is_atomic():
    path = (
        BACKEND_ROOT
        / "app"
        / "modules"
        / "channels"
        / "realtime_ticket.py"
    )

    source = path.read_text(
        encoding="utf-8"
    )

    assert (
        "_ATOMIC_CONSUME_LUA"
        in source
    )

    assert (
        "redis_client.eval("
        in source
    )

    assert (
        "await redis_client.get("
        not in source
    )


def test_websocket_revalidates_membership():
    path = (
        BACKEND_ROOT
        / "app"
        / "modules"
        / "channels"
        / "realtime_websocket.py"
    )

    source = path.read_text(
        encoding="utf-8"
    )

    required = (
        "ChannelAccessGuard",
        "ControlSessionLocal",
        "require_membership_revalidation",
        "code=4403",
        "ChannelRealtimePubSubSession",
        "ChannelRateLimiter",
    )

    for token in required:
        assert token in source