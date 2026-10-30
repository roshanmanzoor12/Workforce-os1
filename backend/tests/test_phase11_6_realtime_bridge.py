from __future__ import annotations

import uuid

from app.modules.realtime_bridge.envelope import (
    build_realtime_envelope,
)
from app.modules.realtime_bridge.redis_transport import (
    DEFAULT_REALTIME_CHANNEL,
)


def test_envelope_event_type() -> None:
    actor = uuid.uuid4()
    recipient = uuid.uuid4()

    envelope = build_realtime_envelope(
        event_type="call.created",
        actor_user_id=actor,
        recipient_user_ids=[
            recipient
        ],
        data={
            "call_id": str(
                uuid.uuid4()
            )
        },
    )

    assert (
        envelope["type"]
        == "call.created"
    )


def test_envelope_actor() -> None:
    actor = uuid.uuid4()

    envelope = build_realtime_envelope(
        event_type=(
            "message.attachments.updated"
        ),
        actor_user_id=actor,
        recipient_user_ids=[],
        data={},
    )

    assert (
        envelope["actor_user_id"]
        == str(actor)
    )


def test_recipient_serialization() -> None:
    first = uuid.uuid4()
    second = uuid.uuid4()

    envelope = build_realtime_envelope(
        event_type="call.signal",
        actor_user_id=uuid.uuid4(),
        recipient_user_ids=[
            first,
            second,
        ],
        data={},
    )

    assert (
        envelope[
            "recipient_user_ids"
        ]
        == [
            str(first),
            str(second),
        ]
    )


def test_envelope_has_unique_id() -> None:
    first = build_realtime_envelope(
        event_type="x",
        actor_user_id=uuid.uuid4(),
        recipient_user_ids=[],
        data={},
    )

    second = build_realtime_envelope(
        event_type="x",
        actor_user_id=uuid.uuid4(),
        recipient_user_ids=[],
        data={},
    )

    assert first["id"] != second["id"]


def test_default_realtime_channel() -> None:
    assert (
        DEFAULT_REALTIME_CHANNEL
        == "workforce:realtime:events"
    )


def test_envelope_has_no_storage_credentials() -> None:
    envelope = build_realtime_envelope(
        event_type="call.signal",
        actor_user_id=uuid.uuid4(),
        recipient_user_ids=[],
        data={
            "candidate": "abc"
        },
    )

    text = str(envelope)

    assert "MINIO_ACCESS_KEY" not in text
    assert "MINIO_SECRET_KEY" not in text
    assert "DATABASE_URL" not in text


def test_envelope_has_created_at() -> None:
    envelope = build_realtime_envelope(
        event_type="call.created",
        actor_user_id=uuid.uuid4(),
        recipient_user_ids=[],
        data={},
    )

    assert envelope["created_at"]