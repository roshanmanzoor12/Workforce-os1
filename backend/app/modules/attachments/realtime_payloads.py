from __future__ import annotations

from app.modules.attachments.models import (
    Attachment,
)


def serialize_attachment_realtime(
    attachment: Attachment,
) -> dict[str, object]:
    return {
        "id": str(
            attachment.id
        ),
        "message_id": (
            str(attachment.message_id)
            if attachment.message_id
            else None
        ),
        "scope": (
            attachment.scope.value
        ),
        "conversation_id": (
            str(
                attachment.conversation_id
            )
            if attachment.conversation_id
            else None
        ),
        "channel_id": (
            str(
                attachment.channel_id
            )
            if attachment.channel_id
            else None
        ),
        "kind": (
            attachment.kind.value
        ),
        "filename": (
            attachment.original_filename
        ),
        "content_type": (
            attachment.content_type
        ),
        "size_bytes": (
            attachment.size_bytes
        ),
    }


def serialize_message_attachments_realtime(
    attachments: list[Attachment],
) -> list[dict[str, object]]:
    return [
        serialize_attachment_realtime(
            attachment
        )
        for attachment in attachments
    ]


def build_attachment_bound_event(
    *,
    message_id: str,
    attachments: list[Attachment],
) -> dict[str, object]:
    return {
        "type": "message.attachments.updated",
        "data": {
            "message_id": message_id,
            "attachments": (
                serialize_message_attachments_realtime(
                    attachments
                )
            ),
        },
    }