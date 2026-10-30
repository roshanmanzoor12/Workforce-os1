from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.modules.monitoring_admin.models import (
    MonitoringAdminPolicy,
)


class MonitoringAdminRepository:
    DEFAULT_POLICY_KEY = "default"

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def get_policy(
        self,
    ) -> MonitoringAdminPolicy | None:
        result = await self.session.execute(
            select(
                MonitoringAdminPolicy
            ).where(
                MonitoringAdminPolicy.policy_key
                == self.DEFAULT_POLICY_KEY
            )
        )

        return result.scalar_one_or_none()

    async def get_or_create_policy(
        self,
    ) -> MonitoringAdminPolicy:
        existing = await self.get_policy()

        if existing is not None:
            return existing

        policy = MonitoringAdminPolicy(
            policy_key=(
                self.DEFAULT_POLICY_KEY
            ),
            monitoring_enabled=True,
            screenshots_enabled=True,
            live_screen_enabled=True,
            screen_share_enabled=True,
            disclosure_required=True,
            explicit_live_consent_required=True,
            visible_live_indicator_required=True,
            screenshot_retention_days=30,
            live_session_max_minutes=60,
            policy_version=1,
        )

        self.session.add(
            policy
        )

        await self.session.flush()

        await self.session.refresh(
            policy
        )

        return policy

    async def refresh(
        self,
        policy: MonitoringAdminPolicy,
    ) -> MonitoringAdminPolicy:
        await self.session.flush()

        await self.session.refresh(
            policy
        )

        return policy


__all__ = [
    "MonitoringAdminRepository",
]