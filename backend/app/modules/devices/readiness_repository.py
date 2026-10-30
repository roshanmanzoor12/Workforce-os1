from __future__ import annotations

import uuid

from sqlalchemy import (
    select,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.modules.desktop_agent.models import (
    DesktopAgentDevice,
)


# =========================================================
# REPOSITORY
# =========================================================


class DeviceReadinessRepository:
    """
    Read-only tenant repository for device readiness.

    Readiness uses the existing DesktopAgentDevice evidence because
    that record owns:

    - employee linkage
    - agent version
    - consent
    - capabilities
    - last heartbeat timestamp
    - disabled state

    No new persistence table is required.
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def list_devices(
        self,
        *,
        employee_ids: (
            frozenset[
                uuid.UUID
            ]
            | None
        ),
    ) -> list[
        DesktopAgentDevice
    ]:
        if (
            employee_ids
            is not None
            and not employee_ids
        ):
            return []

        statement = select(
            DesktopAgentDevice
        )

        if employee_ids is not None:
            statement = (
                statement.where(
                    DesktopAgentDevice
                    .employee_id
                    .in_(
                        tuple(
                            employee_ids
                        )
                    )
                )
            )

        statement = (
            statement.order_by(
                DesktopAgentDevice
                .device_name
                .asc(),

                DesktopAgentDevice
                .created_at
                .asc(),
            )
        )

        result = await (
            self.session.execute(
                statement
            )
        )

        return list(
            result.scalars().all()
        )


__all__ = [
    "DeviceReadinessRepository",
]