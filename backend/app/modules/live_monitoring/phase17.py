from __future__ import annotations

import uuid
from datetime import (
    datetime,
    timedelta,
    timezone,
)

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.attachments.storage import (
    get_attachment_storage,
)
from app.modules.audit_log.schemas import (
    AuditEventCreate,
)
from app.modules.audit_log.service import (
    AuditLogService,
)


SCREENSHOT_MEDIA_URL_SECONDS = 300


SCREENSHOT_ALLOWED_STATUSES = frozenset(
    {
        "pending",
        "completed",
        "denied",
        "expired",
        "failed",
    }
)


def utc_now() -> datetime:
    return datetime.now(
        timezone.utc
    )


def normalize_datetime(
    value: datetime,
) -> datetime:
    if value.tzinfo is None:
        return value.replace(
            tzinfo=timezone.utc
        )

    return value.astimezone(
        timezone.utc
    )


def effective_retention_start(
    *,
    requested_start: datetime | None,
    retention_days: int,
    now: datetime | None = None,
) -> datetime:
    if retention_days < 1:
        raise ValueError(
            "Screenshot retention must "
            "be at least one day."
        )

    resolved_now = normalize_datetime(
        now
        if now is not None
        else utc_now()
    )

    retention_start = (
        resolved_now
        - timedelta(
            days=retention_days
        )
    )

    if requested_start is None:
        return retention_start

    requested_start = normalize_datetime(
        requested_start
    )

    return max(
        retention_start,
        requested_start,
    )


def create_screenshot_download_url(
    *,
    object_key: str,
) -> tuple[
    str,
    int,
]:
    if not object_key.strip():
        raise ValueError(
            "Screenshot object key "
            "is required."
        )

    storage = (
        get_attachment_storage()
    )

    url = storage.create_download_url(
        object_key=object_key,
        expires_seconds=(
            SCREENSHOT_MEDIA_URL_SECONDS
        ),
    )

    return (
        url,
        SCREENSHOT_MEDIA_URL_SECONDS,
    )


async def record_screenshot_audit(
    *,
    control_session: AsyncSession,
    workspace_id: uuid.UUID,
    actor_user_id: uuid.UUID,
    action: str,
    target_id: uuid.UUID | None = None,
    event_data: dict | None = None,
) -> None:
    service = AuditLogService(
        control_session
    )

    try:
        await service.record(
            workspace_id=workspace_id,
            payload=AuditEventCreate(
                actor_user_id=(
                    actor_user_id
                ),
                category="monitoring",
                action=action,
                outcome="success",
                severity="info",
                target_type=(
                    "screenshot"
                ),
                target_id=target_id,
                event_data=(
                    event_data
                    or {}
                ),
            ),
        )

        await (
            control_session.commit()
        )

    except Exception:
        await (
            control_session.rollback()
        )

        raise


__all__ = [
    "SCREENSHOT_MEDIA_URL_SECONDS",
    "SCREENSHOT_ALLOWED_STATUSES",
    "utc_now",
    "normalize_datetime",
    "effective_retention_start",
    "create_screenshot_download_url",
    "record_screenshot_audit",
]