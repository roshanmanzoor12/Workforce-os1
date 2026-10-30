from __future__ import annotations

from dataclasses import dataclass
from datetime import (
    datetime,
    timedelta,
    timezone,
)

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.attachments.binding_repository import (
    AttachmentBindingRepository,
)
from app.modules.attachments.models import (
    AttachmentStatus,
)
from app.modules.attachments.storage import (
    AttachmentStorage,
)


@dataclass(slots=True)
class AttachmentCleanupResult:
    scanned: int
    deleted: int
    failed: int


class AttachmentOrphanCleanupService:
    DEFAULT_AGE_HOURS = 24
    DEFAULT_BATCH_SIZE = 100

    def __init__(
        self,
        *,
        session: AsyncSession,
        storage: AttachmentStorage,
    ) -> None:
        self.session = session
        self.storage = storage

        self.repository = (
            AttachmentBindingRepository(
                session
            )
        )

    async def run_once(
        self,
        *,
        age_hours: int = DEFAULT_AGE_HOURS,
        batch_size: int = DEFAULT_BATCH_SIZE,
    ) -> AttachmentCleanupResult:
        if age_hours < 1:
            raise ValueError(
                "age_hours must be >= 1."
            )

        if batch_size < 1:
            raise ValueError(
                "batch_size must be >= 1."
            )

        cutoff = (
            datetime.now(timezone.utc)
            - timedelta(
                hours=age_hours
            )
        )

        attachments = (
            await self.repository
            .list_orphan_pending(
                older_than=cutoff,
                limit=batch_size,
            )
        )

        deleted = 0
        failed = 0

        for attachment in attachments:
            try:
                exists = (
                    self.storage.object_exists(
                        object_key=(
                            attachment.object_key
                        )
                    )
                )

                if exists:
                    self.storage.delete_object(
                        object_key=(
                            attachment.object_key
                        )
                    )

                attachment.status = (
                    AttachmentStatus.DELETED
                )

                attachment.deleted_at = (
                    datetime.now(
                        timezone.utc
                    )
                )

                attachment.failure_reason = (
                    "Expired unbound upload "
                    "removed by orphan cleanup."
                )

                deleted += 1

            except Exception as exc:
                attachment.status = (
                    AttachmentStatus.FAILED
                )

                attachment.failure_reason = (
                    "Orphan cleanup failed: "
                    + str(exc)[:500]
                )

                failed += 1

        await self.session.commit()

        return AttachmentCleanupResult(
            scanned=len(
                attachments
            ),
            deleted=deleted,
            failed=failed,
        )