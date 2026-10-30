from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.modules.website_tracking.privacy import (
    WebsiteTrackingPrivacyPolicy,
)
from app.modules.website_tracking.repository import (
    WebsiteTrackingRepository,
)
from app.modules.website_tracking.schemas import (
    WebsiteObservationProcessingResult,
    WebsiteObservationRequest,
)
from app.modules.website_tracking.service import (
    WebsiteTrackingService,
)


class WebsiteTrackingCoordinator:
    def __init__(
        self,
        session: AsyncSession,
        *,
        privacy_policy: (
            WebsiteTrackingPrivacyPolicy
            | None
        ) = None,
    ) -> None:
        repository = (
            WebsiteTrackingRepository(
                session
            )
        )

        self._service = (
            WebsiteTrackingService(
                repository,
                privacy_policy=privacy_policy,
            )
        )

    async def record_observation(
        self,
        *,
        device_id: uuid.UUID,
        employee_id: uuid.UUID | None,
        request: WebsiteObservationRequest,
    ) -> WebsiteObservationProcessingResult:
        return await self._service.record_observation(
            device_id=device_id,
            employee_id=employee_id,
            request=request,
        )


__all__ = [
    "WebsiteTrackingCoordinator",
]