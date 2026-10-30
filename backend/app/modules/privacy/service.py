from __future__ import annotations

from uuid import UUID, uuid4

from app.modules.privacy.models import (
    PrivacyExclusion,
    PrivacyPolicy,
    PrivacyZone,
)
from app.modules.privacy.repository import PrivacyRepository


class PrivacyItemNotFoundError(LookupError):
    pass


class PrivacyService:
    def __init__(
        self,
        repository: PrivacyRepository | None = None,
    ) -> None:
        self.repository = (
            repository
            if repository is not None
            else PrivacyRepository()
        )

    async def list_policies(
        self,
        workspace_id: UUID,
    ) -> list[PrivacyPolicy]:
        return await self.repository.list_policies(workspace_id)

    async def create_policy(
        self,
        workspace_id: UUID,
        name: str,
        description: str | None,
    ) -> PrivacyPolicy:
        item = PrivacyPolicy(
            id=uuid4(),
            workspace_id=workspace_id,
            name=name,
            description=description,
        )

        return await self.repository.save_policy(item)

    async def list_zones(
        self,
        workspace_id: UUID,
    ) -> list[PrivacyZone]:
        return await self.repository.list_zones(workspace_id)

    async def create_zone(
        self,
        workspace_id: UUID,
        name: str,
        zone_type: str,
        value: str,
    ) -> PrivacyZone:
        item = PrivacyZone(
            id=uuid4(),
            workspace_id=workspace_id,
            name=name,
            zone_type=zone_type,
            value=value,
        )

        return await self.repository.save_zone(item)

    async def list_exclusions(
        self,
        workspace_id: UUID,
    ) -> list[PrivacyExclusion]:
        return await self.repository.list_exclusions(workspace_id)

    async def create_exclusion(
        self,
        workspace_id: UUID,
        exclusion_type: str,
        value: str,
        reason: str | None,
    ) -> PrivacyExclusion:
        item = PrivacyExclusion(
            id=uuid4(),
            workspace_id=workspace_id,
            exclusion_type=exclusion_type,
            value=value,
            reason=reason,
        )

        return await self.repository.save_exclusion(item)