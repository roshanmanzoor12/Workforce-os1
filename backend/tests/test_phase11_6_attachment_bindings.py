from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.modules.attachments.binding_schemas import (
    AttachmentBindRequest,
)
from app.modules.attachments.models import (
    AttachmentKind,
    AttachmentScope,
)
from app.modules.attachments.realtime_payloads import (
    build_attachment_bound_event,
    serialize_attachment_realtime,
)


def fake_attachment():
    return SimpleNamespace(
        id=uuid.uuid4(),
        message_id=uuid.uuid4(),
        scope=(
            AttachmentScope.CONVERSATION
        ),
        conversation_id=uuid.uuid4(),
        channel_id=None,
        kind=AttachmentKind.IMAGE,
        original_filename=(
            "screenshot.png"
        ),
        content_type="image/png",
        size_bytes=12345,
        ready_at=datetime.now(
            timezone.utc
        ),
    )


def test_bind_request_accepts_one() -> None:
    attachment_id = uuid.uuid4()

    request = AttachmentBindRequest(
        attachment_ids=[
            attachment_id
        ]
    )

    assert request.attachment_ids == [
        attachment_id
    ]


def test_bind_request_rejects_empty() -> None:
    with pytest.raises(
        ValidationError
    ):
        AttachmentBindRequest(
            attachment_ids=[]
        )


def test_bind_request_rejects_more_than_10() -> None:
    with pytest.raises(
        ValidationError
    ):
        AttachmentBindRequest(
            attachment_ids=[
                uuid.uuid4()
                for _ in range(11)
            ]
        )


def test_realtime_attachment_payload() -> None:
    attachment = fake_attachment()

    payload = (
        serialize_attachment_realtime(
            attachment
        )
    )

    assert payload["id"] == str(
        attachment.id
    )

    assert payload["message_id"] == str(
        attachment.message_id
    )

    assert (
        payload["scope"]
        == "CONVERSATION"
    )

    assert payload["kind"] == "IMAGE"

    assert (
        payload["filename"]
        == "screenshot.png"
    )


def test_attachment_event_name() -> None:
    attachment = fake_attachment()

    event = build_attachment_bound_event(
        message_id=str(
            attachment.message_id
        ),
        attachments=[
            attachment
        ],
    )

    assert (
        event["type"]
        == "message.attachments.updated"
    )


def test_attachment_event_contains_message() -> None:
    attachment = fake_attachment()

    event = build_attachment_bound_event(
        message_id=str(
            attachment.message_id
        ),
        attachments=[
            attachment
        ],
    )

    assert (
        event["data"]["message_id"]
        == str(
            attachment.message_id
        )
    )


def test_attachment_event_contains_items() -> None:
    attachment = fake_attachment()

    event = build_attachment_bound_event(
        message_id=str(
            attachment.message_id
        ),
        attachments=[
            attachment
        ],
    )

    assert (
        len(
            event["data"][
                "attachments"
            ]
        )
        == 1
    )


def test_channel_scope_serialization() -> None:
    attachment = fake_attachment()

    attachment.scope = (
        AttachmentScope.CHANNEL
    )

    attachment.conversation_id = None
    attachment.channel_id = uuid.uuid4()

    payload = (
        serialize_attachment_realtime(
            attachment
        )
    )

    assert (
        payload["scope"]
        == "CHANNEL"
    )

    assert (
        payload["conversation_id"]
        is None
    )

    assert (
        payload["channel_id"]
        == str(
            attachment.channel_id
        )
    )


def test_download_url_not_in_realtime_payload() -> None:
    attachment = fake_attachment()

    payload = (
        serialize_attachment_realtime(
            attachment
        )
    )

    assert "download_url" not in payload
    assert "upload_url" not in payload


def test_storage_credentials_not_in_payload() -> None:
    attachment = fake_attachment()

    payload = (
        serialize_attachment_realtime(
            attachment
        )
    )

    assert "access_key" not in payload
    assert "secret_key" not in payload
    assert "bucket_name" not in payload
    assert "object_key" not in payload