from __future__ import annotations

from dataclasses import dataclass
from datetime import (
    datetime,
    timedelta,
    timezone,
)

from sqlalchemy import (
    select,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.core.storage import (
    delete_object,
)
from app.modules.live_monitoring.models import (
    ScreenshotCaptureRequest,
)


@dataclass(
    frozen=True,
    slots=True,
)
class ScreenshotRetentionResult:
    cutoff_at: datetime

    scanned: int

    deleted: int

    storage_failures: int

    database_failures: int

    has_more: bool


def utc_now() -> datetime:
    return datetime.now(
        timezone.utc
    )


def retention_cutoff(
    *,
    retention_days: int,
    now: datetime | None = None,
) -> datetime:
    if retention_days < 1:
        raise ValueError(
            "Screenshot retention must "
            "be at least one day."
        )

    resolved_now = (
        now
        if now is not None
        else utc_now()
    )

    if (
        resolved_now.tzinfo
        is None
    ):
        resolved_now = (
            resolved_now.replace(
                tzinfo=timezone.utc
            )
        )

    return (
        resolved_now
        - timedelta(
            days=retention_days
        )
    )


class ScreenshotRetentionService:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def cleanup(
        self,
        *,
        retention_days: int,
        now: datetime | None = None,
        limit: int = 500,
    ) -> ScreenshotRetentionResult:
        if limit < 1:
            raise ValueError(
                "Cleanup limit must be "
                "at least one."
            )

        cutoff = retention_cutoff(
            retention_days=(
                retention_days
            ),
            now=now,
        )

        # Read one extra item so callers know whether another
        # batch remains without scanning the whole table.

        statement = (
            select(
                ScreenshotCaptureRequest
            )
            .where(
                ScreenshotCaptureRequest
                .requested_at
                < cutoff
            )
            .order_by(
                ScreenshotCaptureRequest
                .requested_at
                .asc(),
                ScreenshotCaptureRequest
                .id
                .asc(),
            )
            .limit(
                limit + 1
            )
        )

        result = await (
            self.session.execute(
                statement
            )
        )

        items = list(
            result.scalars().all()
        )

        has_more = (
            len(items)
            > limit
        )

        candidates = items[
            :limit
        ]

        deleted = 0

        storage_failures = 0

        database_failures = 0

        for item in candidates:
            object_key = (
                item.storage_object_key
            )

            # Physical media is deleted first.
            #
            # If object-storage deletion fails, preserve the
            # database record so the cleanup remains retryable.

            if object_key:
                try:
                    delete_object(
                        object_key=(
                            object_key
                        )
                    )

                except Exception:
                    storage_failures += 1

                    continue

            try:
                await self.session.delete(
                    item
                )

                await (
                    self.session.flush()
                )

                # Commit one candidate at a time so a later
                # storage/database failure does not roll back
                # already-completed retention work.

                await (
                    self.session.commit()
                )

                deleted += 1

            except Exception:
                database_failures += 1

                await (
                    self.session.rollback()
                )

        return ScreenshotRetentionResult(
            cutoff_at=cutoff,

            scanned=len(
                candidates
            ),

            deleted=deleted,

            storage_failures=(
                storage_failures
            ),

            database_failures=(
                database_failures
            ),

            has_more=has_more,
        )


__all__ = [
    "ScreenshotRetentionResult",
    "ScreenshotRetentionService",
    "utc_now",
    "retention_cutoff",
]