from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy import (
    Select,
    func,
    or_,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.devices.models import Device
from app.modules.employees.models import Employee


class DeviceRepository:
    """
    Tenant-scoped persistence layer for registered devices.

    This repository only works with the already-authorized tenant
    AsyncSession provided by the request/service layer.
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    # =====================================================
    # CREATE
    # =====================================================

    async def create_device(
        self,
        *,
        hostname: str,
        os_name: str,
        os_version: str | None = None,
        architecture: str | None = None,
        agent_version: str | None = None,
        agent_identifier: str | None = None,
        employee_id: uuid.UUID | None = None,
        device_uuid: uuid.UUID | None = None,
        status: str,
        is_active: bool = True,
        first_seen_at=None,
        last_seen_at=None,
        registered_at=None,
        monitoring_profile_id: uuid.UUID | None = None,
    ) -> Device:
        device = Device(
            device_uuid=(
                device_uuid
                if device_uuid is not None
                else uuid.uuid4()
            ),
            employee_id=employee_id,
            hostname=hostname,
            os_name=os_name,
            os_version=os_version,
            architecture=architecture,
            agent_version=agent_version,
            agent_identifier=agent_identifier,
            status=status,
            is_active=is_active,
            first_seen_at=first_seen_at,
            last_seen_at=last_seen_at,
            registered_at=registered_at,
            monitoring_profile_id=monitoring_profile_id,
        )

        self.session.add(
            device
        )

        await self.session.flush()

        return device

    # =====================================================
    # GETTERS
    # =====================================================

    async def get_device_by_id(
        self,
        device_id: uuid.UUID,
    ) -> Device | None:
        result = await self.session.execute(
            select(
                Device
            ).where(
                Device.id == device_id
            )
        )

        return result.scalar_one_or_none()

    async def get_device_by_uuid(
        self,
        device_uuid: uuid.UUID,
    ) -> Device | None:
        result = await self.session.execute(
            select(
                Device
            ).where(
                Device.device_uuid
                == device_uuid
            )
        )

        return result.scalar_one_or_none()

    async def get_device_by_agent_identifier(
        self,
        agent_identifier: str,
    ) -> Device | None:
        result = await self.session.execute(
            select(
                Device
            ).where(
                Device.agent_identifier
                == agent_identifier
            )
        )

        return result.scalar_one_or_none()

    # =====================================================
    # EMPLOYEE VALIDATION
    # =====================================================

    async def get_employee_by_id(
        self,
        employee_id: uuid.UUID,
    ) -> Employee | None:
        result = await self.session.execute(
            select(
                Employee
            ).where(
                Employee.id == employee_id
            )
        )

        return result.scalar_one_or_none()

    async def get_active_employee_by_id(
        self,
        employee_id: uuid.UUID,
    ) -> Employee | None:
        result = await self.session.execute(
            select(
                Employee
            ).where(
                Employee.id == employee_id,
                Employee.is_active.is_(True),
            )
        )

        return result.scalar_one_or_none()

    # =====================================================
    # EXISTENCE / DUPLICATE CHECKS
    # =====================================================

    async def device_uuid_exists(
        self,
        device_uuid: uuid.UUID,
        *,
        exclude_device_id: uuid.UUID | None = None,
    ) -> bool:
        statement = select(
            func.count(
                Device.id
            )
        ).where(
            Device.device_uuid
            == device_uuid
        )

        if exclude_device_id is not None:
            statement = statement.where(
                Device.id
                != exclude_device_id
            )

        result = await self.session.execute(
            statement
        )

        return bool(
            result.scalar_one()
        )

    async def agent_identifier_exists(
        self,
        agent_identifier: str,
        *,
        exclude_device_id: uuid.UUID | None = None,
    ) -> bool:
        statement = select(
            func.count(
                Device.id
            )
        ).where(
            Device.agent_identifier
            == agent_identifier
        )

        if exclude_device_id is not None:
            statement = statement.where(
                Device.id
                != exclude_device_id
            )

        result = await self.session.execute(
            statement
        )

        return bool(
            result.scalar_one()
        )

    # =====================================================
    # LIST / SEARCH
    # =====================================================

    async def list_devices(
        self,
        *,
        employee_id: uuid.UUID | None = None,
        status: str | None = None,
        include_inactive: bool = False,
        search: str | None = None,
    ) -> list[Device]:
        statement = self._build_device_list_statement(
            employee_id=employee_id,
            status=status,
            include_inactive=include_inactive,
            search=search,
        ).order_by(
            Device.hostname.asc(),
            Device.created_at.asc(),
        )

        result = await self.session.execute(
            statement
        )

        return list(
            result.scalars().all()
        )

    async def count_devices(
        self,
        *,
        employee_id: uuid.UUID | None = None,
        status: str | None = None,
        include_inactive: bool = False,
        search: str | None = None,
    ) -> int:
        filters = []

        if employee_id is not None:
            filters.append(
                Device.employee_id
                == employee_id
            )

        if status is not None:
            filters.append(
                Device.status
                == status
            )

        if not include_inactive:
            filters.append(
                Device.is_active.is_(True)
            )

        if search:
            normalized_search = (
                f"%{search.strip().lower()}%"
            )

            filters.append(
                or_(
                    func.lower(
                        Device.hostname
                    ).like(
                        normalized_search
                    ),
                    func.lower(
                        Device.os_name
                    ).like(
                        normalized_search
                    ),
                    func.lower(
                        Device.os_version
                    ).like(
                        normalized_search
                    ),
                    func.lower(
                        Device.agent_version
                    ).like(
                        normalized_search
                    ),
                    func.lower(
                        Device.agent_identifier
                    ).like(
                        normalized_search
                    ),
                )
            )

        statement = select(
            func.count(
                Device.id
            )
        )

        if filters:
            statement = statement.where(
                *filters
            )

        result = await self.session.execute(
            statement
        )

        return int(
            result.scalar_one()
        )

    def _build_device_list_statement(
        self,
        *,
        employee_id: uuid.UUID | None,
        status: str | None,
        include_inactive: bool,
        search: str | None,
    ) -> Select:
        statement = select(
            Device
        )

        if employee_id is not None:
            statement = statement.where(
                Device.employee_id
                == employee_id
            )

        if status is not None:
            statement = statement.where(
                Device.status
                == status
            )

        if not include_inactive:
            statement = statement.where(
                Device.is_active.is_(True)
            )

        if search:
            normalized_search = (
                f"%{search.strip().lower()}%"
            )

            statement = statement.where(
                or_(
                    func.lower(
                        Device.hostname
                    ).like(
                        normalized_search
                    ),
                    func.lower(
                        Device.os_name
                    ).like(
                        normalized_search
                    ),
                    func.lower(
                        Device.os_version
                    ).like(
                        normalized_search
                    ),
                    func.lower(
                        Device.agent_version
                    ).like(
                        normalized_search
                    ),
                    func.lower(
                        Device.agent_identifier
                    ).like(
                        normalized_search
                    ),
                )
            )

        return statement

    # =====================================================
    # EMPLOYEE DEVICE LIST
    # =====================================================

    async def list_employee_devices(
        self,
        employee_id: uuid.UUID,
        *,
        include_inactive: bool = False,
    ) -> Sequence[Device]:
        statement = select(
            Device
        ).where(
            Device.employee_id
            == employee_id
        )

        if not include_inactive:
            statement = statement.where(
                Device.is_active.is_(True)
            )

        statement = statement.order_by(
            Device.created_at.asc()
        )

        result = await self.session.execute(
            statement
        )

        return result.scalars().all()

    # =====================================================
    # UPDATE
    # =====================================================

    async def update_device(
        self,
        device: Device,
        *,
        values: dict,
    ) -> Device:
        for field_name, value in values.items():
            setattr(
                device,
                field_name,
                value,
            )

        await self.session.flush()

        return device

    # =====================================================
    # ASSIGNMENT
    # =====================================================

    async def assign_employee(
        self,
        device: Device,
        *,
        employee_id: uuid.UUID | None,
    ) -> Device:
        device.employee_id = (
            employee_id
        )

        await self.session.flush()

        return device

    # =====================================================
    # REVOCATION / DEACTIVATION
    # =====================================================

    async def revoke_device(
        self,
        device: Device,
        *,
        revoked_at,
        revoked_status: str,
    ) -> Device:
        device.status = (
            revoked_status
        )

        device.is_active = False
        device.revoked_at = revoked_at

        await self.session.flush()

        return device

    # =====================================================
    # STATUS / HEARTBEAT PREPARATION
    # =====================================================

    async def update_device_presence(
        self,
        device: Device,
        *,
        status: str,
        last_seen_at,
        agent_version: str | None = None,
    ) -> Device:
        device.status = status
        device.last_seen_at = (
            last_seen_at
        )

        if agent_version is not None:
            device.agent_version = (
                agent_version
            )

        await self.session.flush()

        return device


__all__ = [
    "DeviceRepository",
]