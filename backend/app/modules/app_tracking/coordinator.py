from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.app_tracking.models import (
    AppObservation,
)
from app.modules.app_tracking.repository import (
    AppTrackingRepository,
)
from app.modules.app_tracking.schemas import (
    AppObservationRequest,
    AppObservationResponse,
)
from app.modules.app_tracking.service import (
    AppTrackingService,
)


class AppTrackingCoordinator:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self._repository = (
            AppTrackingRepository(
                session
            )
        )

        self._service = (
            AppTrackingService(
                self._repository
            )
        )

    async def record_observation(
        self,
        *,
        device_id: UUID,
        device_uuid: UUID,
        employee_id: UUID | None,
        payload: AppObservationRequest,
    ) -> AppObservationResponse:
        app_key = (
            self._service.build_app_key(
                payload.process_name,
                payload.executable_path,
            )
        )

        received_at = datetime.now(
            timezone.utc
        )

        observation = AppObservation(
            device_id=device_id,
            employee_id=employee_id,
            app_key=app_key,
            process_name=payload.process_name,
            executable_path=payload.executable_path,
            window_title=payload.window_title,
            observed_at=payload.observed_at,
            received_at=received_at,
        )

        observation = (
            await self._repository.create_observation(
                observation
            )
        )

        await self._service.process_observation(
            observation
        )

        return AppObservationResponse(
            event_id=observation.id,
            device_uuid=device_uuid,
            employee_id=employee_id,
            app_key=observation.app_key,
            process_name=observation.process_name,
            executable_path=observation.executable_path,
            window_title=observation.window_title,
            observed_at=observation.observed_at,
            received_at=observation.received_at,
        )


__all__ = [
    "AppTrackingCoordinator",
]