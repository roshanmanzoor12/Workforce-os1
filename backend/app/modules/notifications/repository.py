from __future__ import annotations

import uuid
from datetime import (
    datetime,
    timezone,
)

from sqlalchemy import (
    func,
    select,
    update,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.modules.notifications.models import (
    Notification,
    NotificationPreference,
)


class NotificationRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    # =====================================================
    # NOTIFICATIONS
    # =====================================================

    async def create(
        self,
        notification: Notification,
    ) -> Notification:
        self.session.add(
            notification
        )

        await self.session.flush()

        await self.session.refresh(
            notification
        )

        return notification

    async def get_for_recipient(
        self,
        *,
        notification_id: uuid.UUID,
        recipient_user_id: uuid.UUID,
    ) -> Notification | None:
        result = await self.session.execute(
            select(
                Notification
            ).where(
                Notification.id
                == notification_id,
                Notification.recipient_user_id
                == recipient_user_id,
            )
        )

        return (
            result
            .scalar_one_or_none()
        )

    async def list_for_recipient(
        self,
        *,
        recipient_user_id: uuid.UUID,
        unread_only: bool,
        notification_type: str | None,
        limit: int,
        offset: int,
    ) -> tuple[
        list[Notification],
        int,
    ]:
        filters = [
            Notification.recipient_user_id
            == recipient_user_id
        ]

        if unread_only:
            filters.append(
                Notification.read_at.is_(
                    None
                )
            )

        if notification_type:
            filters.append(
                Notification.notification_type
                == notification_type
            )

        count_result = (
            await self.session.execute(
                select(
                    func.count(
                        Notification.id
                    )
                ).where(
                    *filters
                )
            )
        )

        total = int(
            count_result.scalar_one()
            or 0
        )

        result = await self.session.execute(
            select(
                Notification
            )
            .where(
                *filters
            )
            .order_by(
                Notification.created_at
                .desc(),
                Notification.id.desc(),
            )
            .limit(
                limit
            )
            .offset(
                offset
            )
        )

        return (
            list(
                result
                .scalars()
                .all()
            ),
            total,
        )

    async def unread_count(
        self,
        *,
        recipient_user_id: uuid.UUID,
    ) -> int:
        result = await self.session.execute(
            select(
                func.count(
                    Notification.id
                )
            ).where(
                Notification.recipient_user_id
                == recipient_user_id,
                Notification.read_at.is_(
                    None
                ),
            )
        )

        return int(
            result.scalar_one()
            or 0
        )

    async def mark_read(
        self,
        *,
        notification: Notification,
    ) -> Notification:
        if notification.read_at is None:
            notification.read_at = (
                datetime.now(
                    timezone.utc
                )
            )

            await self.session.flush()

            await self.session.refresh(
                notification
            )

        return notification

    async def mark_unread(
        self,
        *,
        notification: Notification,
    ) -> Notification:
        if notification.read_at is not None:
            notification.read_at = None

            await self.session.flush()

            await self.session.refresh(
                notification
            )

        return notification

    async def mark_all_read(
        self,
        *,
        recipient_user_id: uuid.UUID,
    ) -> int:
        now = datetime.now(
            timezone.utc
        )

        result = await self.session.execute(
            update(
                Notification
            )
            .where(
                Notification.recipient_user_id
                == recipient_user_id,
                Notification.read_at.is_(
                    None
                ),
            )
            .values(
                read_at=now
            )
        )

        return int(
            result.rowcount
            or 0
        )

    # =====================================================
    async def list_for_user(self, *, user_id: uuid.UUID, unread_only: bool = False, notification_type: str | None = None, limit: int = 50, offset: int = 0):
        return await self.list_for_recipient(recipient_user_id=user_id, unread_only=unread_only, notification_type=notification_type, limit=limit, offset=offset)

    async def count_unread(self, *, user_id: uuid.UUID) -> int:
        return await self.unread_count(recipient_user_id=user_id)

    async def get_for_user(self, *, notification_id: uuid.UUID, user_id: uuid.UUID):
        return await self.get_for_recipient(notification_id=notification_id, recipient_user_id=user_id)

    async def delete_for_user(self, *, notification_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        notification = await self.get_for_user(notification_id=notification_id, user_id=user_id)
        if notification is None:
            return False
        await self.session.delete(notification)
        await self.session.flush()
        return True

    # PREFERENCES
    # =====================================================

    async def get_preferences(
        self,
        *,
        user_id: uuid.UUID,
    ) -> (
        NotificationPreference
        | None
    ):
        result = await self.session.execute(
            select(
                NotificationPreference
            ).where(
                NotificationPreference.user_id
                == user_id
            )
        )

        return (
            result
            .scalar_one_or_none()
        )

    async def get_or_create_preferences(
        self,
        *,
        user_id: uuid.UUID,
    ) -> NotificationPreference:
        existing = await (
            self.get_preferences(
                user_id=user_id
            )
        )

        if existing is not None:
            return existing

        preference = (
            NotificationPreference(
                user_id=user_id,
                in_app_enabled=True,
                email_enabled=True,
                push_enabled=True,
                sound_enabled=True,
                digest_enabled=False,
                digest_hour=8,
                muted_types=[],
            )
        )

        self.session.add(
            preference
        )

        await self.session.flush()

        await self.session.refresh(
            preference
        )

        return preference


__all__ = [
    "NotificationRepository",
]

