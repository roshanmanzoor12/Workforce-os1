from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ResourceNotFound,
    ValidationError,
)
from app.modules.devices.credential_models import (
    DEVICE_CREDENTIAL_STATUS_ACTIVE,
    DEVICE_CREDENTIAL_STATUS_EXPIRED,
    DEVICE_CREDENTIAL_STATUS_REVOKED,
    DeviceCredential,
)
from app.modules.devices.credential_repository import (
    DeviceCredentialRepository,
)
from app.modules.devices.credential_schemas import (
    AuthenticatedDeviceCredential,
    DeviceAuthenticationRequest,
    DeviceCredentialIssueResult,
    DeviceCredentialListResponse,
    DeviceCredentialPublic,
    DeviceCredentialRevokeResponse,
    DeviceCredentialRotationResponse,
)
from app.modules.devices.models import (
    DEVICE_STATUS_REVOKED,
    Device,
)
from app.modules.devices.repository import (
    DeviceRepository,
)


# =========================================================
# DEVICE SECRET FORMAT
# =========================================================

DEVICE_SECRET_PREFIX = "wfds"

DEVICE_SECRET_RANDOM_BYTES = 32

DEVICE_SECRET_DISPLAY_PREFIX_LENGTH = 12


# =========================================================
# DEVICE CREDENTIAL SERVICE
# =========================================================


class DeviceCredentialService:
    """
    Tenant-local authentication service for registered devices.

    Lifecycle:

        activation code
            -> initial enrollment only

        device_uuid + device_secret
            -> ongoing device authentication

    Security properties:

    - plaintext device_secret is returned only when issued
    - plaintext device_secret is never persisted
    - only SHA-256 secret_hash is stored
    - secrets are generated from cryptographically secure randomness
    - credentials may be rotated
    - revoked/expired credentials cannot authenticate
    - revoked devices cannot authenticate even with a valid secret
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

        self.repository = (
            DeviceCredentialRepository(
                session
            )
        )

        self.device_repository = (
            DeviceRepository(
                session
            )
        )

    # =====================================================
    # TIME
    # =====================================================

    @staticmethod
    def _now() -> datetime:
        return datetime.now(
            timezone.utc
        )

    # =====================================================
    # SECRET GENERATION
    # =====================================================

    @staticmethod
    def _generate_device_secret() -> str:
        """
        Generate a high-entropy secret returned once to the agent.

        Example:

            wfds_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
        """

        random_part = secrets.token_urlsafe(
            DEVICE_SECRET_RANDOM_BYTES
        )

        return (
            f"{DEVICE_SECRET_PREFIX}_"
            f"{random_part}"
        )

    # =====================================================
    # SECRET NORMALIZATION
    # =====================================================

    @staticmethod
    def _normalize_device_secret(
        device_secret: str,
    ) -> str:
        normalized = device_secret.strip()

        if not normalized:
            raise ValidationError(
                "Device secret is required."
            )

        if len(normalized) > 255:
            raise ValidationError(
                "Invalid device credentials."
            )

        return normalized

    # =====================================================
    # HASHING
    # =====================================================

    @staticmethod
    def hash_device_secret(
        device_secret: str,
    ) -> str:
        """
        Hash a high-entropy device secret for deterministic lookup.

        Device secrets contain strong random entropy, so SHA-256
        provides an appropriate non-plaintext lookup representation.
        """

        normalized = device_secret.strip()

        return hashlib.sha256(
            normalized.encode(
                "utf-8"
            )
        ).hexdigest()

    # =====================================================
    # DISPLAY PREFIX
    # =====================================================

    @staticmethod
    def _build_secret_prefix(
        device_secret: str,
    ) -> str:
        return device_secret[
            :DEVICE_SECRET_DISPLAY_PREFIX_LENGTH
        ]

    # =====================================================
    # MAPPERS
    # =====================================================

    @staticmethod
    def _to_public(
        credential: DeviceCredential,
    ) -> DeviceCredentialPublic:
        return (
            DeviceCredentialPublic.model_validate(
                credential
            )
        )

    # =====================================================
    # DEVICE LOOKUPS
    # =====================================================

    async def _require_device(
        self,
        device_id: uuid.UUID,
    ) -> Device:
        device = (
            await self.device_repository.get_device_by_id(
                device_id
            )
        )

        if device is None:
            raise ResourceNotFound(
                "Device not found."
            )

        return device

    async def _require_authenticatable_device(
        self,
        device_id: uuid.UUID,
    ) -> Device:
        device = await self._require_device(
            device_id
        )

        if not device.is_active:
            raise ResourceNotFound(
                "Device authentication failed."
            )

        if (
            device.status
            == DEVICE_STATUS_REVOKED
        ):
            raise ResourceNotFound(
                "Device authentication failed."
            )

        return device

    # =====================================================
    # CREDENTIAL LOOKUPS
    # =====================================================

    async def _require_credential(
        self,
        credential_id: uuid.UUID,
    ) -> DeviceCredential:
        credential = (
            await self.repository.get_by_id(
                credential_id
            )
        )

        if credential is None:
            raise ResourceNotFound(
                "Device credential not found."
            )

        return credential

    # =====================================================
    # EXPIRATION
    # =====================================================

    @staticmethod
    def _is_expired(
        credential: DeviceCredential,
        *,
        now: datetime,
    ) -> bool:
        if credential.expires_at is None:
            return False

        return (
            credential.expires_at
            <= now
        )

    async def _expire_if_needed(
        self,
        credential: DeviceCredential,
        *,
        now: datetime,
        commit: bool = True,
    ) -> bool:
        if (
            credential.status
            != DEVICE_CREDENTIAL_STATUS_ACTIVE
        ):
            return False

        if not credential.is_active:
            return False

        if not self._is_expired(
            credential,
            now=now,
        ):
            return False

        await self.repository.expire_credential(
            credential,
            expired_status=(
                DEVICE_CREDENTIAL_STATUS_EXPIRED
            ),
        )

        if commit:
            await self.session.commit()

        return True

    # =====================================================
    # GENERATE UNIQUE SECRET
    # =====================================================

    async def _generate_unique_secret(
        self,
    ) -> tuple[str, str]:
        """
        Generate plaintext secret + unique persisted hash.

        Collision probability is negligible, but persistence should
        not depend on probability alone.
        """

        for _ in range(5):
            device_secret = (
                self._generate_device_secret()
            )

            secret_hash = (
                self.hash_device_secret(
                    device_secret
                )
            )

            exists = (
                await self.repository.secret_hash_exists(
                    secret_hash
                )
            )

            if not exists:
                return (
                    device_secret,
                    secret_hash,
                )

        raise ValidationError(
            "Unable to generate a unique "
            "device credential."
        )

    # =====================================================
    # INITIAL CREDENTIAL ISSUE
    # =====================================================

    async def issue_initial_credential(
        self,
        *,
        device_id: uuid.UUID,
        expires_at: datetime | None = None,
    ) -> DeviceCredentialIssueResult:
        """
        Issue the first credential for a newly registered device.

        Intended to run immediately after trusted device enrollment.
        """

        device = (
            await self._require_authenticatable_device(
                device_id
            )
        )

        now = self._now()

        if (
            expires_at is not None
            and expires_at <= now
        ):
            raise ValidationError(
                "Device credential expiration "
                "must be in the future."
            )

        existing = (
            await self.repository.list_device_credentials(
                device.id,
                include_inactive=True,
            )
        )

        if existing:
            raise ValidationError(
                "Device already has credentials."
            )

        (
            device_secret,
            secret_hash,
        ) = await self._generate_unique_secret()

        credential = (
            await self.repository.create_credential(
                device_id=device.id,
                secret_hash=secret_hash,
                secret_prefix=(
                    self._build_secret_prefix(
                        device_secret
                    )
                ),
                version=1,
                status=(
                    DEVICE_CREDENTIAL_STATUS_ACTIVE
                ),
                is_active=True,
                issued_at=now,
                expires_at=expires_at,
            )
        )

        await self.session.commit()

        await self.session.refresh(
            credential
        )

        return DeviceCredentialIssueResult(
            device_secret=device_secret,
            credential=self._to_public(
                credential
            ),
        )

    # =====================================================
    # AUTHENTICATE DEVICE
    # =====================================================

    async def authenticate_device(
        self,
        payload: DeviceAuthenticationRequest,
    ) -> AuthenticatedDeviceCredential:
        """
        Authenticate one agent inside an already-trusted tenant.

        Tenant routing must be resolved before this service is called.

        Authentication requires BOTH:

            device_uuid
            device_secret

        A secret belonging to another device is rejected.
        """

        normalized_secret = (
            self._normalize_device_secret(
                payload.device_secret
            )
        )

        secret_hash = (
            self.hash_device_secret(
                normalized_secret
            )
        )

        credential = (
            await self.repository.get_active_by_hash(
                secret_hash
            )
        )

        if credential is None:
            raise ResourceNotFound(
                "Device authentication failed."
            )

        now = self._now()

        expired = (
            await self._expire_if_needed(
                credential,
                now=now,
            )
        )

        if expired:
            raise ResourceNotFound(
                "Device authentication failed."
            )

        if (
            credential.status
            != DEVICE_CREDENTIAL_STATUS_ACTIVE
            or not credential.is_active
        ):
            raise ResourceNotFound(
                "Device authentication failed."
            )

        device = (
            await self._require_authenticatable_device(
                credential.device_id
            )
        )

        if (
            device.device_uuid
            != payload.device_uuid
        ):
            raise ResourceNotFound(
                "Device authentication failed."
            )

        await self.repository.mark_used(
            credential,
            used_at=now,
        )

        await self.session.commit()

        return AuthenticatedDeviceCredential(
            device_id=device.id,
            device_uuid=device.device_uuid,
            credential_id=credential.id,
            credential_version=(
                credential.version
            ),
        )

    # =====================================================
    # ROTATE CREDENTIAL
    # =====================================================

    async def rotate_credential(
        self,
        *,
        device_id: uuid.UUID,
        expires_at: datetime | None = None,
    ) -> DeviceCredentialRotationResponse:
        """
        Rotate a device credential.

        Existing active credentials are locked and revoked before
        the replacement credential is created.
        """

        device = (
            await self._require_authenticatable_device(
                device_id
            )
        )

        now = self._now()

        if (
            expires_at is not None
            and expires_at <= now
        ):
            raise ValidationError(
                "Device credential expiration "
                "must be in the future."
            )

        active_credentials = (
            await self.repository.get_active_device_credentials_for_update(
                device.id
            )
        )

        next_version = (
            await self.repository.get_next_version(
                device.id
            )
        )

        (
            device_secret,
            secret_hash,
        ) = await self._generate_unique_secret()

        if active_credentials:
            await self.repository.revoke_credentials(
                active_credentials,
                revoked_at=now,
                revoked_status=(
                    DEVICE_CREDENTIAL_STATUS_REVOKED
                ),
            )

        credential = (
            await self.repository.create_credential(
                device_id=device.id,
                secret_hash=secret_hash,
                secret_prefix=(
                    self._build_secret_prefix(
                        device_secret
                    )
                ),
                version=next_version,
                status=(
                    DEVICE_CREDENTIAL_STATUS_ACTIVE
                ),
                is_active=True,
                issued_at=now,
                expires_at=expires_at,
            )
        )

        await self.session.commit()

        await self.session.refresh(
            credential
        )

        return DeviceCredentialRotationResponse(
            message=(
                "Device credential rotated."
            ),
            device_secret=device_secret,
            credential=self._to_public(
                credential
            ),
        )

    # =====================================================
    # REVOKE ONE CREDENTIAL
    # =====================================================

    async def revoke_credential(
        self,
        *,
        device_id: uuid.UUID,
        credential_id: uuid.UUID,
    ) -> DeviceCredentialRevokeResponse:
        await self._require_device(
            device_id
        )

        credential = (
            await self._require_credential(
                credential_id
            )
        )

        if (
            credential.device_id
            != device_id
        ):
            raise ResourceNotFound(
                "Device credential not found."
            )

        if (
            credential.status
            == DEVICE_CREDENTIAL_STATUS_REVOKED
        ):
            return DeviceCredentialRevokeResponse(
                message=(
                    "Device credential revoked."
                ),
                success=True,
            )

        await self.repository.revoke_credential(
            credential,
            revoked_at=self._now(),
            revoked_status=(
                DEVICE_CREDENTIAL_STATUS_REVOKED
            ),
        )

        await self.session.commit()

        return DeviceCredentialRevokeResponse(
            message=(
                "Device credential revoked."
            ),
            success=True,
        )

    # =====================================================
    # REVOKE ALL DEVICE CREDENTIALS
    # =====================================================

    async def revoke_all_device_credentials(
        self,
        *,
        device_id: uuid.UUID,
    ) -> DeviceCredentialRevokeResponse:
        await self._require_device(
            device_id
        )

        active_credentials = (
            await self.repository.get_active_device_credentials_for_update(
                device_id
            )
        )

        if active_credentials:
            await self.repository.revoke_credentials(
                active_credentials,
                revoked_at=self._now(),
                revoked_status=(
                    DEVICE_CREDENTIAL_STATUS_REVOKED
                ),
            )

            await self.session.commit()

        return DeviceCredentialRevokeResponse(
            message=(
                "Device credentials revoked."
            ),
            success=True,
        )

    # =====================================================
    # LIST CREDENTIAL HISTORY
    # =====================================================

    async def list_credentials(
        self,
        *,
        device_id: uuid.UUID,
        include_inactive: bool = True,
    ) -> DeviceCredentialListResponse:
        await self._require_device(
            device_id
        )

        credentials = (
            await self.repository.list_device_credentials(
                device_id,
                include_inactive=include_inactive,
            )
        )

        now = self._now()
        changed = False

        for credential in credentials:
            expired = (
                await self._expire_if_needed(
                    credential,
                    now=now,
                    commit=False,
                )
            )

            if expired:
                changed = True

        if changed:
            await self.session.commit()

            if not include_inactive:
                credentials = (
                    await self.repository.list_device_credentials(
                        device_id,
                        include_inactive=False,
                    )
                )

        return DeviceCredentialListResponse(
            credentials=[
                self._to_public(
                    credential
                )
                for credential in credentials
            ],
            total=len(
                credentials
            ),
        )


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "DEVICE_SECRET_PREFIX",
    "DEVICE_SECRET_RANDOM_BYTES",
    "DEVICE_SECRET_DISPLAY_PREFIX_LENGTH",
    "DeviceCredentialService",
]