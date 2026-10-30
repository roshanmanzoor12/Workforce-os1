from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    func,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.desktop_agent.models import (
    DesktopAgentDevice,
)


class DesktopAgentRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def get(
        self,
        *,
        device_id: uuid.UUID,
    ) -> DesktopAgentDevice | None:
        result = await self.session.execute(
            select(
                DesktopAgentDevice
            ).where(
                DesktopAgentDevice.id
                == device_id
            )
        )

        return (
            result
            .scalar_one_or_none()
        )

    async def get_by_installation_id(
        self,
        *,
        installation_id: uuid.UUID,
    ) -> DesktopAgentDevice | None:
        result = await self.session.execute(
            select(
                DesktopAgentDevice
            ).where(
                DesktopAgentDevice
                .installation_id
                == installation_id
            )
        )

        return (
            result
            .scalar_one_or_none()
        )

    async def create(
        self,
        *,
        device: DesktopAgentDevice,
    ) -> DesktopAgentDevice:
        self.session.add(
            device
        )

        await self.session.flush()

        await self.session.refresh(
            device
        )

        return device

    async def refresh(
        self,
        *,
        device: DesktopAgentDevice,
    ) -> DesktopAgentDevice:
        await self.session.flush()

        await self.session.refresh(
            device
        )

        return device

    async def list(
        self,
        *,
        employee_ids: (
            frozenset[uuid.UUID]
            | None
        ),
        status: str | None,
        limit: int,
        offset: int,
    ) -> tuple[
        list[DesktopAgentDevice],
        int,
    ]:
        filters = []

        if employee_ids is not None:
            if not employee_ids:
                return (
                    [],
                    0,
                )

            filters.append(
                DesktopAgentDevice
                .employee_id
                .in_(
                    tuple(
                        employee_ids
                    )
                )
            )

        if status is not None:
            filters.append(
                DesktopAgentDevice.status
                == status
            )

        count_statement = select(
            func.count(
                DesktopAgentDevice.id
            )
        )

        if filters:
            count_statement = (
                count_statement.where(
                    *filters
                )
            )

        count_result = await (
            self.session.execute(
                count_statement
            )
        )

        total = int(
            count_result.scalar_one()
        )

        statement = (
            select(
                DesktopAgentDevice
            )
            .order_by(
                DesktopAgentDevice
                .last_seen_at
                .desc(),

                DesktopAgentDevice
                .id
                .asc(),
            )
            .limit(
                limit
            )
            .offset(
                offset
            )
        )

        if filters:
            statement = statement.where(
                *filters
            )

        result = await self.session.execute(
            statement
        )

        return (
            list(
                result
                .scalars()
                .all()
            ),
            total,
        )

    async def mark_seen(
        self,
        *,
        device: DesktopAgentDevice,
        seen_at: datetime,
        agent_version: str | None,
        os_version: str | None,
        ip_address: str | None,
    ) -> DesktopAgentDevice:
        device.last_seen_at = seen_at

        if not device.is_disabled:
            device.status = "online"

        if agent_version is not None:
            device.agent_version = (
                agent_version
            )

        if os_version is not None:
            device.os_version = os_version

        if ip_address is not None:
            device.last_ip_address = (
                ip_address
            )

        return await self.refresh(
            device=device
        )

    async def disable(
        self,
        *,
        device: DesktopAgentDevice,
    ) -> DesktopAgentDevice:
        device.is_disabled = True
        device.status = "disabled"

        return await self.refresh(
            device=device
        )


__all__ = [
    "DesktopAgentRepository",
]