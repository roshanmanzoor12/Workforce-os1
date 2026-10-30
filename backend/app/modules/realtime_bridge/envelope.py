from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(
        timezone.utc
    ).isoformat()


def build_realtime_envelope(
    *,
    event_type: str,
    actor_user_id: uuid.UUID,
    data: dict[str, Any],
    recipient_user_ids: list[uuid.UUID],
) -> dict[str, Any]:
    return {
        "id": str(uuid.uuid4()),
        "type": event_type,
        "actor_user_id": str(
            actor_user_id
        ),
        "recipient_user_ids": [
            str(user_id)
            for user_id
            in recipient_user_ids
        ],
        "created_at": utc_now_iso(),
        "data": data,
    }