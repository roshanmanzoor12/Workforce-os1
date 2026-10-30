from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    func,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.devices.credential_models import (
    DeviceCredential,
)


class DeviceCredentialRepository:
    """
    Tenant-scoped persistence layer for device credentials.

    Responsibilities:
    - create credential records
    - resolve credentials by hash/id
    - lock credentials during sensitive lifecycle changes
    - list credential history for a device
    - calculate next credential version
    - revoke old credentials
    - update last-used timestamps

    Plaintext device secrets never enter this repository.
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    # =====================================================
    # CREATE
    # =====================================================

    async def create_credential(
        self,
        *,
        device_id: uuid.UUID,
        secret_hash: str,
        secret_prefix: str | None,
        version: int,
        status: str,
        is_active: bool,
        issued_at: datetime | None,
        expires_at: datetime | None,
    ) -> DeviceCredential:
        credential = DeviceCredential(
            device_id=device_id,
            secret_hash=secret_hash,
            secret_prefix=secret_prefix,
            version=version,
            status=status,
            is_active=is_active,
            issued_at=issued_at,
            expires_at=expires_at,
        )

        self.session.add(
            credential
        )

        await self.session.flush()

        return credential

    # =====================================================
    # GETTERS
    # =====================================================

    async def get_by_id(
        self,
        credential_id: uuid.UUID,
    ) -> DeviceCredential | None:
        result = await self.session.execute(
            select(
                DeviceCredential
            ).where(
                DeviceCredential.id
                == credential_id
            )
        )

        return result.scalar_one_or_none()

    async def get_by_hash(
        self,
        secret_hash: str,
    ) -> DeviceCredential | None:
        result = await self.session.execute(
            select(
                DeviceCredential
            ).where(
                DeviceCredential.secret_hash
                == secret_hash
            )
        )

        return result.scalar_one_or_none()

    async def get_active_by_hash(
        self,
        secret_hash: str,
    ) -> DeviceCredential | None:
        result = await self.session.execute(
            select(
                DeviceCredential
            ).where(
                DeviceCredential.secret_hash
                == secret_hash,
                DeviceCredential.is_active.is_(
                    True
                ),
            )
        )

        return result.scalar_one_or_none()

    # =====================================================
    # LOCKED GETTERS
    # =====================================================

    async def get_by_id_for_update(
        self,
        credential_id: uuid.UUID,
    ) -> DeviceCredential | None:
        """
        Lock one credential row until the current transaction ends.
        """

        result = await self.session.execute(
            select(
                DeviceCredential
            )
            .where(
                DeviceCredential.id
                == credential_id
            )
            .with_for_update()
        )

        return result.scalar_one_or_none()

    async def get_active_device_credentials_for_update(
        self,
        device_id: uuid.UUID,
    ) -> list[DeviceCredential]:
        """
        Lock all active credentials for one device.

        Used during credential rotation so concurrent rotations
        cannot both leave multiple active credentials behind.
        """

        result = await self.session.execute(
            select(
                DeviceCredential
            )
            .where(
                DeviceCredential.device_id
                == device_id,
                DeviceCredential.is_active.is_(
                    True
                ),
            )
            .order_by(
                DeviceCredential.version.asc()
            )
            .with_for_update()
        )

        return list(
            result.scalars().all()
        )

    # =====================================================
    # LIST
    # =====================================================

    async def list_device_credentials(
        self,
        device_id: uuid.UUID,
        *,
        include_inactive: bool = True,
    ) -> list[DeviceCredential]:
        statement = select(
            DeviceCredential
        ).where(
            DeviceCredential.device_id
            == device_id
        )

        if not include_inactive:
            statement = statement.where(
                DeviceCredential.is_active.is_(
                    True
                )
            )

        statement = statement.order_by(
            DeviceCredential.version.desc()
        )

        result = await self.session.execute(
            statement
        )

        return list(
            result.scalars().all()
        )

    async def count_device_credentials(
        self,
        device_id: uuid.UUID,
        *,
        include_inactive: bool = True,
    ) -> int:
        statement = select(
            func.count(
                DeviceCredential.id
            )
        ).where(
            DeviceCredential.device_id
            == device_id
        )

        if not include_inactive:
            statement = statement.where(
                DeviceCredential.is_active.is_(
                    True
                )
            )

        result = await self.session.execute(
            statement
        )

        return int(
            result.scalar_one()
        )

    # =====================================================
    # VERSIONING
    # =====================================================

    async def get_next_version(
        self,
        device_id: uuid.UUID,
    ) -> int:
        """
        Return the next credential version for one device.

        Caller should perform rotation while holding appropriate
        device/credential locks when concurrency matters.
        """

        result = await self.session.execute(
            select(
                func.max(
                    DeviceCredential.version
                )
            ).where(
                DeviceCredential.device_id
                == device_id
            )
        )

        current_max = (
            result.scalar_one_or_none()
        )

        if current_max is None:
            return 1

        return int(
            current_max
        ) + 1

    # =====================================================
    # HASH EXISTENCE
    # =====================================================

    async def secret_hash_exists(
        self,
        secret_hash: str,
    ) -> bool:
        result = await self.session.execute(
            select(
                func.count(
                    DeviceCredential.id
                )
            ).where(
                DeviceCredential.secret_hash
                == secret_hash
            )
        )

        return bool(
            result.scalar_one()
        )

    # =====================================================
    # USAGE
    # =====================================================

    async def mark_used(
        self,
        credential: DeviceCredential,
        *,
        used_at: datetime,
    ) -> DeviceCredential:
        credential.last_used_at = (
            used_at
        )

        await self.session.flush()

        return credential

    # =====================================================
    # REVOKE
    # =====================================================

    async def revoke_credential(
        self,
        credential: DeviceCredential,
        *,
        revoked_at: datetime,
        revoked_status: str,
    ) -> DeviceCredential:
        credential.status = (
            revoked_status
        )

        credential.is_active = False
        credential.revoked_at = (
            revoked_at
        )

        await self.session.flush()

        return credential

    async def revoke_credentials(
        self,
        credentials: list[
            DeviceCredential
        ],
        *,
        revoked_at: datetime,
        revoked_status: str,
    ) -> None:
        for credential in credentials:
            credential.status = (
                revoked_status
            )

            credential.is_active = False
            credential.revoked_at = (
                revoked_at
            )

        await self.session.flush()

    # =====================================================
    # EXPIRE
    # =====================================================

    async def expire_credential(
        self,
        credential: DeviceCredential,
        *,
        expired_status: str,
    ) -> DeviceCredential:
        credential.status = (
            expired_status
        )

        credential.is_active = False

        await self.session.flush()

        return credential

    # =====================================================
    # GENERIC UPDATE
    # =====================================================

    async def update_credential(
        self,
        credential: DeviceCredential,
        *,
        values: dict[str, object],
    ) -> DeviceCredential:
        for field_name, value in values.items():
            setattr(
                credential,
                field_name,
                value,
            )

        await self.session.flush()

        return credential


__all__ = [
    "DeviceCredentialRepository",
]