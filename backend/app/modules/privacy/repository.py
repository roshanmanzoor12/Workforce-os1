from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from app.modules.privacy.models import (
    PrivacyExclusion,
    PrivacyPolicy,
    PrivacyZone,
)


class PrivacyRepository:
    def __init__(self) -> None:
        self.policies: dict[UUID, PrivacyPolicy] = {}
        self.zones: dict[UUID, PrivacyZone] = {}
        self.exclusions: dict[UUID, PrivacyExclusion] = {}

    async def list_policies(
        self,
        workspace_id: UUID,
    ) -> list[PrivacyPolicy]:
        return [
            item
            for item in self.policies.values()
            if item.workspace_id == workspace_id
        ]

    async def get_policy(
        self,
        workspace_id: UUID,
        policy_id: UUID,
    ) -> PrivacyPolicy | None:
        item = self.policies.get(policy_id)

        if item is None or item.workspace_id != workspace_id:
            return None

        return item

    async def save_policy(
        self,
        item: PrivacyPolicy,
    ) -> PrivacyPolicy:
        item.updated_at = datetime.now(timezone.utc)
        self.policies[item.id] = item
        return item

    async def list_zones(
        self,
        workspace_id: UUID,
    ) -> list[PrivacyZone]:
        return [
            item
            for item in self.zones.values()
            if item.workspace_id == workspace_id
        ]

    async def get_zone(
        self,
        workspace_id: UUID,
        zone_id: UUID,
    ) -> PrivacyZone | None:
        item = self.zones.get(zone_id)

        if item is None or item.workspace_id != workspace_id:
            return None

        return item

    async def save_zone(
        self,
        item: PrivacyZone,
    ) -> PrivacyZone:
        item.updated_at = datetime.now(timezone.utc)
        self.zones[item.id] = item
        return item

    async def list_exclusions(
        self,
        workspace_id: UUID,
    ) -> list[PrivacyExclusion]:
        return [
            item
            for item in self.exclusions.values()
            if item.workspace_id == workspace_id
        ]

    async def get_exclusion(
        self,
        workspace_id: UUID,
        exclusion_id: UUID,
    ) -> PrivacyExclusion | None:
        item = self.exclusions.get(exclusion_id)

        if item is None or item.workspace_id != workspace_id:
            return None

        return item

    async def save_exclusion(
        self,
        item: PrivacyExclusion,
    ) -> PrivacyExclusion:
        item.updated_at = datetime.now(timezone.utc)
        self.exclusions[item.id] = item
        return item