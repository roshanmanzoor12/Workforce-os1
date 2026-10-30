from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    func,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.devices.activation_models import (
    DeviceActivationCode,
)


class DeviceActivationRepository:
    """
    Control-plane persistence layer for device activation codes.

    Important:
    - runs against the shared control database
    - plaintext activation codes are never stored
    - workspace binding is trusted server-side control data
    - locking helpers exist for concurrency-safe activation use
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    # =====================================================
    # CREATE
    # =====================================================

    async def create_activation_code(
        self,
        *,
        workspace_id: uuid.UUID,
        created_by_user_id: uuid.UUID,
        code_hash: str,
        code_prefix: str | None,
        status: str,
        is_active: bool,
        expires_at: datetime | None,
        max_uses: int | None,
        used_count: int,
        label: str | None,
    ) -> DeviceActivationCode:
        activation = DeviceActivationCode(
            workspace_id=workspace_id,
            created_by_user_id=created_by_user_id,
            code_hash=code_hash,
            code_prefix=code_prefix,
            status=status,
            is_active=is_active,
            expires_at=expires_at,
            max_uses=max_uses,
            used_count=used_count,
            label=label,
        )

        self.session.add(
            activation
        )

        await self.session.flush()

        return activation

    # =====================================================
    # GETTERS
    # =====================================================

    async def get_by_id(
        self,
        activation_id: uuid.UUID,
    ) -> DeviceActivationCode | None:
        result = await self.session.execute(
            select(
                DeviceActivationCode
            ).where(
                DeviceActivationCode.id
                == activation_id
            )
        )

        return result.scalar_one_or_none()

    async def get_by_hash(
        self,
        code_hash: str,
    ) -> DeviceActivationCode | None:
        result = await self.session.execute(
            select(
                DeviceActivationCode
            ).where(
                DeviceActivationCode.code_hash
                == code_hash
            )
        )

        return result.scalar_one_or_none()

    # =====================================================
    # LOCKED GETTERS
    # =====================================================

    async def get_by_id_for_update(
        self,
        activation_id: uuid.UUID,
    ) -> DeviceActivationCode | None:
        """
        Fetch one activation row and lock it until transaction end.

        Used for concurrency-sensitive lifecycle transitions such as
        usage consumption.
        """

        result = await self.session.execute(
            select(
                DeviceActivationCode
            )
            .where(
                DeviceActivationCode.id
                == activation_id
            )
            .with_for_update()
        )

        return result.scalar_one_or_none()

    async def get_workspace_activation_for_update(
        self,
        *,
        activation_id: uuid.UUID,
        workspace_id: uuid.UUID,
    ) -> DeviceActivationCode | None:
        """
        Lock exactly one workspace-bound activation row.

        This prevents two concurrent registrations from both reading
        the same pre-increment used_count and exceeding max_uses.
        """

        result = await self.session.execute(
            select(
                DeviceActivationCode
            )
            .where(
                DeviceActivationCode.id
                == activation_id,
                DeviceActivationCode.workspace_id
                == workspace_id,
            )
            .with_for_update()
        )

        return result.scalar_one_or_none()

    # =====================================================
    # WORKSPACE OWNERSHIP
    # =====================================================

    async def get_workspace_activation_by_id(
        self,
        *,
        activation_id: uuid.UUID,
        workspace_id: uuid.UUID,
    ) -> DeviceActivationCode | None:
        result = await self.session.execute(
            select(
                DeviceActivationCode
            ).where(
                DeviceActivationCode.id
                == activation_id,
                DeviceActivationCode.workspace_id
                == workspace_id,
            )
        )

        return result.scalar_one_or_none()

    # =====================================================
    # LIST
    # =====================================================

    async def list_workspace_activation_codes(
        self,
        workspace_id: uuid.UUID,
        *,
        include_inactive: bool = False,
    ) -> list[DeviceActivationCode]:
        statement = select(
            DeviceActivationCode
        ).where(
            DeviceActivationCode.workspace_id
            == workspace_id
        )

        if not include_inactive:
            statement = statement.where(
                DeviceActivationCode.is_active.is_(True)
            )

        statement = statement.order_by(
            DeviceActivationCode.created_at.desc()
        )

        result = await self.session.execute(
            statement
        )

        return list(
            result.scalars().all()
        )

    async def count_workspace_activation_codes(
        self,
        workspace_id: uuid.UUID,
        *,
        include_inactive: bool = False,
    ) -> int:
        statement = select(
            func.count(
                DeviceActivationCode.id
            )
        ).where(
            DeviceActivationCode.workspace_id
            == workspace_id
        )

        if not include_inactive:
            statement = statement.where(
                DeviceActivationCode.is_active.is_(True)
            )

        result = await self.session.execute(
            statement
        )

        return int(
            result.scalar_one()
        )

    # =====================================================
    # HASH EXISTENCE
    # =====================================================

    async def code_hash_exists(
        self,
        code_hash: str,
    ) -> bool:
        result = await self.session.execute(
            select(
                func.count(
                    DeviceActivationCode.id
                )
            ).where(
                DeviceActivationCode.code_hash
                == code_hash
            )
        )

        return bool(
            result.scalar_one()
        )

    # =====================================================
    # USAGE
    # =====================================================

    async def increment_usage(
        self,
        activation: DeviceActivationCode,
        *,
        used_at: datetime,
    ) -> DeviceActivationCode:
        activation.used_count += 1
        activation.last_used_at = used_at

        await self.session.flush()

        return activation

    # =====================================================
    # GENERIC UPDATE
    # =====================================================

    async def update_activation(
        self,
        activation: DeviceActivationCode,
        *,
        values: dict[str, object],
    ) -> DeviceActivationCode:
        for field_name, value in values.items():
            setattr(
                activation,
                field_name,
                value,
            )

        await self.session.flush()

        return activation

    # =====================================================
    # LIFECYCLE
    # =====================================================

    async def mark_expired(
        self,
        activation: DeviceActivationCode,
        *,
        expired_status: str,
    ) -> DeviceActivationCode:
        activation.status = expired_status
        activation.is_active = False

        await self.session.flush()

        return activation

    async def mark_exhausted(
        self,
        activation: DeviceActivationCode,
        *,
        exhausted_status: str,
    ) -> DeviceActivationCode:
        activation.status = exhausted_status
        activation.is_active = False

        await self.session.flush()

        return activation

    async def revoke_activation(
        self,
        activation: DeviceActivationCode,
        *,
        revoked_at: datetime,
        revoked_status: str,
    ) -> DeviceActivationCode:
        activation.status = revoked_status
        activation.is_active = False
        activation.revoked_at = revoked_at

        await self.session.flush()

        return activation


__all__ = [
    "DeviceActivationRepository",
]