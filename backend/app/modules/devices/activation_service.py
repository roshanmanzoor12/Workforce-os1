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
from app.modules.devices.activation_models import (
    ACTIVATION_STATUS_ACTIVE,
    ACTIVATION_STATUS_EXHAUSTED,
    ACTIVATION_STATUS_EXPIRED,
    ACTIVATION_STATUS_REVOKED,
    DeviceActivationCode,
)
from app.modules.devices.activation_repository import (
    DeviceActivationRepository,
)
from app.modules.devices.activation_schemas import (
    DeviceActivationCodeCreateRequest,
    DeviceActivationCodeCreateResponse,
    DeviceActivationCodeListResponse,
    DeviceActivationCodePublic,
    DeviceActivationCodeResponse,
    DeviceActivationCodeRevokeResponse,
    ResolvedDeviceActivation,
)


# =========================================================
# ACTIVATION CODE FORMAT
# =========================================================

ACTIVATION_CODE_PREFIX = "wfdev"

ACTIVATION_CODE_RANDOM_BYTES = 24

ACTIVATION_CODE_DISPLAY_PREFIX_LENGTH = 12


class DeviceActivationService:
    """
    Control-plane service for endpoint activation codes.

    Security model:

        admin creates activation code
            ↓
        plaintext returned once
            ↓
        SHA-256 hash stored in control DB
            ↓
        agent submits activation code
            ↓
        trusted workspace resolution
            ↓
        successful device registration
            ↓
        activation usage consumed atomically

    Activation codes are enrollment secrets only.
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

        self.repository = (
            DeviceActivationRepository(
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
    # NORMALIZATION
    # =====================================================

    @staticmethod
    def _normalize_code(
        activation_code: str,
    ) -> str:
        normalized = activation_code.strip()

        if not normalized:
            raise ValidationError(
                "Device activation code is required."
            )

        if len(normalized) > 200:
            raise ValidationError(
                "Invalid device activation code."
            )

        return normalized

    # =====================================================
    # GENERATION
    # =====================================================

    @staticmethod
    def _generate_activation_code() -> str:
        random_part = secrets.token_urlsafe(
            ACTIVATION_CODE_RANDOM_BYTES
        )

        return (
            f"{ACTIVATION_CODE_PREFIX}_"
            f"{random_part}"
        )

    # =====================================================
    # HASHING
    # =====================================================

    @staticmethod
    def hash_activation_code(
        activation_code: str,
    ) -> str:
        normalized = activation_code.strip()

        return hashlib.sha256(
            normalized.encode(
                "utf-8"
            )
        ).hexdigest()

    # =====================================================
    # DISPLAY PREFIX
    # =====================================================

    @staticmethod
    def _build_code_prefix(
        activation_code: str,
    ) -> str:
        return activation_code[
            :ACTIVATION_CODE_DISPLAY_PREFIX_LENGTH
        ]

    # =====================================================
    # MAPPER
    # =====================================================

    @staticmethod
    def _to_public(
        activation: DeviceActivationCode,
    ) -> DeviceActivationCodePublic:
        return (
            DeviceActivationCodePublic.model_validate(
                activation
            )
        )

    # =====================================================
    # LOOKUPS
    # =====================================================

    async def _require_activation(
        self,
        activation_id: uuid.UUID,
    ) -> DeviceActivationCode:
        activation = (
            await self.repository.get_by_id(
                activation_id
            )
        )

        if activation is None:
            raise ResourceNotFound(
                "Device activation code not found."
            )

        return activation

    async def _require_workspace_activation(
        self,
        *,
        workspace_id: uuid.UUID,
        activation_id: uuid.UUID,
    ) -> DeviceActivationCode:
        activation = (
            await self.repository.get_workspace_activation_by_id(
                activation_id=activation_id,
                workspace_id=workspace_id,
            )
        )

        if activation is None:
            raise ResourceNotFound(
                "Device activation code not found."
            )

        return activation

    async def _require_workspace_activation_for_update(
        self,
        *,
        workspace_id: uuid.UUID,
        activation_id: uuid.UUID,
    ) -> DeviceActivationCode:
        """
        Fetch and lock one activation row until transaction end.

        This is required for atomic usage-limit enforcement.
        """

        activation = (
            await self.repository.get_workspace_activation_for_update(
                activation_id=activation_id,
                workspace_id=workspace_id,
            )
        )

        if activation is None:
            raise ResourceNotFound(
                "Device activation code not found."
            )

        return activation

    # =====================================================
    # STATE HELPERS
    # =====================================================

    @staticmethod
    def _is_expired(
        activation: DeviceActivationCode,
        *,
        now: datetime,
    ) -> bool:
        if activation.expires_at is None:
            return False

        return (
            activation.expires_at
            <= now
        )

    @staticmethod
    def _is_exhausted(
        activation: DeviceActivationCode,
    ) -> bool:
        if activation.max_uses is None:
            return False

        return (
            activation.used_count
            >= activation.max_uses
        )

    # =====================================================
    # CREATE
    # =====================================================

    async def create_activation_code(
        self,
        payload: DeviceActivationCodeCreateRequest,
        *,
        workspace_id: uuid.UUID,
        created_by_user_id: uuid.UUID,
    ) -> DeviceActivationCodeCreateResponse:
        now = self._now()

        if (
            payload.expires_at is not None
            and payload.expires_at <= now
        ):
            raise ValidationError(
                "Activation-code expiration must "
                "be in the future."
            )

        activation_code: str
        code_hash: str

        for _ in range(5):
            activation_code = (
                self._generate_activation_code()
            )

            code_hash = (
                self.hash_activation_code(
                    activation_code
                )
            )

            exists = (
                await self.repository.code_hash_exists(
                    code_hash
                )
            )

            if not exists:
                break

        else:
            raise ValidationError(
                "Unable to generate a unique "
                "device activation code."
            )

        activation = (
            await self.repository.create_activation_code(
                workspace_id=workspace_id,
                created_by_user_id=created_by_user_id,
                code_hash=code_hash,
                code_prefix=self._build_code_prefix(
                    activation_code
                ),
                status=ACTIVATION_STATUS_ACTIVE,
                is_active=True,
                expires_at=payload.expires_at,
                max_uses=payload.max_uses,
                used_count=0,
                label=payload.label,
            )
        )

        await self.session.commit()

        await self.session.refresh(
            activation
        )

        return DeviceActivationCodeCreateResponse(
            message=(
                "Device activation code created."
            ),
            activation_code=activation_code,
            activation=self._to_public(
                activation
            ),
        )

    # =====================================================
    # GET
    # =====================================================

    async def get_activation_code(
        self,
        *,
        workspace_id: uuid.UUID,
        activation_id: uuid.UUID,
    ) -> DeviceActivationCodeResponse:
        activation = (
            await self._require_workspace_activation(
                workspace_id=workspace_id,
                activation_id=activation_id,
            )
        )

        await self._synchronize_lifecycle(
            activation
        )

        return DeviceActivationCodeResponse(
            activation=self._to_public(
                activation
            )
        )

    # =====================================================
    # LIST
    # =====================================================

    async def list_activation_codes(
        self,
        *,
        workspace_id: uuid.UUID,
        include_inactive: bool = False,
    ) -> DeviceActivationCodeListResponse:
        activations = (
            await self.repository.list_workspace_activation_codes(
                workspace_id,
                include_inactive=include_inactive,
            )
        )

        lifecycle_changed = False

        for activation in activations:
            changed = (
                await self._synchronize_lifecycle(
                    activation,
                    commit=False,
                )
            )

            if changed:
                lifecycle_changed = True

        if lifecycle_changed:
            await self.session.commit()

        if (
            lifecycle_changed
            and not include_inactive
        ):
            activations = (
                await self.repository.list_workspace_activation_codes(
                    workspace_id,
                    include_inactive=False,
                )
            )

        return DeviceActivationCodeListResponse(
            activation_codes=[
                self._to_public(
                    activation
                )
                for activation in activations
            ],
            total=len(
                activations
            ),
        )

    # =====================================================
    # RESOLVE
    # =====================================================

    async def resolve_activation_code(
        self,
        activation_code: str,
    ) -> ResolvedDeviceActivation:
        """
        Resolve an activation secret to a trusted workspace.

        This method intentionally does not increment used_count.

        Consumption occurs only after tenant-side device registration
        succeeds.
        """

        normalized = (
            self._normalize_code(
                activation_code
            )
        )

        code_hash = (
            self.hash_activation_code(
                normalized
            )
        )

        activation = (
            await self.repository.get_by_hash(
                code_hash
            )
        )

        if activation is None:
            raise ResourceNotFound(
                "Device activation code is invalid."
            )

        await self._synchronize_lifecycle(
            activation
        )

        if (
            not activation.is_active
            or activation.status
            != ACTIVATION_STATUS_ACTIVE
        ):
            raise ValidationError(
                "Device activation code is not active."
            )

        return ResolvedDeviceActivation(
            activation_id=activation.id,
            workspace_id=activation.workspace_id,
            status=activation.status,
            expires_at=activation.expires_at,
            max_uses=activation.max_uses,
            used_count=activation.used_count,
        )

    # =====================================================
    # CONSUME
    # =====================================================

    async def consume_activation_code(
        self,
        *,
        activation_id: uuid.UUID,
        workspace_id: uuid.UUID,
    ) -> ResolvedDeviceActivation:
        """
        Atomically consume one successful device enrollment.

        A PostgreSQL row lock is acquired before checking:

            status
            is_active
            expires_at
            max_uses
            used_count

        Therefore two concurrent registrations cannot both consume
        the final allowed use.
        """

        activation = (
            await self._require_workspace_activation_for_update(
                workspace_id=workspace_id,
                activation_id=activation_id,
            )
        )

        now = self._now()

        # -------------------------------------------------
        # EXPIRY CHECK WHILE LOCKED
        # -------------------------------------------------

        if self._is_expired(
            activation,
            now=now,
        ):
            await self.repository.mark_expired(
                activation,
                expired_status=(
                    ACTIVATION_STATUS_EXPIRED
                ),
            )

            await self.session.commit()

            raise ValidationError(
                "Device activation code has expired."
            )

        # -------------------------------------------------
        # EXISTING STATE CHECK
        # -------------------------------------------------

        if (
            not activation.is_active
            or activation.status
            != ACTIVATION_STATUS_ACTIVE
        ):
            await self.session.rollback()

            raise ValidationError(
                "Device activation code is not active."
            )

        # -------------------------------------------------
        # LIMIT CHECK BEFORE INCREMENT
        # -------------------------------------------------

        if self._is_exhausted(
            activation
        ):
            await self.repository.mark_exhausted(
                activation,
                exhausted_status=(
                    ACTIVATION_STATUS_EXHAUSTED
                ),
            )

            await self.session.commit()

            raise ValidationError(
                "Device activation code usage limit "
                "has been reached."
            )

        # -------------------------------------------------
        # INCREMENT
        # -------------------------------------------------

        await self.repository.increment_usage(
            activation,
            used_at=now,
        )

        # -------------------------------------------------
        # MARK EXHAUSTED ON FINAL VALID USE
        # -------------------------------------------------

        if self._is_exhausted(
            activation
        ):
            await self.repository.mark_exhausted(
                activation,
                exhausted_status=(
                    ACTIVATION_STATUS_EXHAUSTED
                ),
            )

        await self.session.commit()

        await self.session.refresh(
            activation
        )

        return ResolvedDeviceActivation(
            activation_id=activation.id,
            workspace_id=activation.workspace_id,
            status=activation.status,
            expires_at=activation.expires_at,
            max_uses=activation.max_uses,
            used_count=activation.used_count,
        )

    # =====================================================
    # REVOKE
    # =====================================================

    async def revoke_activation_code(
        self,
        *,
        workspace_id: uuid.UUID,
        activation_id: uuid.UUID,
    ) -> DeviceActivationCodeRevokeResponse:
        activation = (
            await self._require_workspace_activation(
                workspace_id=workspace_id,
                activation_id=activation_id,
            )
        )

        if (
            activation.status
            == ACTIVATION_STATUS_REVOKED
        ):
            return DeviceActivationCodeRevokeResponse(
                message=(
                    "Device activation code revoked."
                ),
                success=True,
            )

        await self.repository.revoke_activation(
            activation,
            revoked_at=self._now(),
            revoked_status=(
                ACTIVATION_STATUS_REVOKED
            ),
        )

        await self.session.commit()

        return DeviceActivationCodeRevokeResponse(
            message=(
                "Device activation code revoked."
            ),
            success=True,
        )

    # =====================================================
    # LIFECYCLE SYNCHRONIZATION
    # =====================================================

    async def _synchronize_lifecycle(
        self,
        activation: DeviceActivationCode,
        *,
        commit: bool = True,
    ) -> bool:
        """
        Lazily transition active codes to expired/exhausted states.

        Concurrency-sensitive consumption does not rely on this
        helper alone; consume_activation_code performs its checks
        again while holding a database row lock.
        """

        if (
            activation.status
            != ACTIVATION_STATUS_ACTIVE
        ):
            return False

        if not activation.is_active:
            return False

        now = self._now()

        if self._is_expired(
            activation,
            now=now,
        ):
            await self.repository.mark_expired(
                activation,
                expired_status=(
                    ACTIVATION_STATUS_EXPIRED
                ),
            )

            if commit:
                await self.session.commit()

                await self.session.refresh(
                    activation
                )

            return True

        if self._is_exhausted(
            activation
        ):
            await self.repository.mark_exhausted(
                activation,
                exhausted_status=(
                    ACTIVATION_STATUS_EXHAUSTED
                ),
            )

            if commit:
                await self.session.commit()

                await self.session.refresh(
                    activation
                )

            return True

        return False


__all__ = [
    "ACTIVATION_CODE_PREFIX",
    "ACTIVATION_CODE_RANDOM_BYTES",
    "ACTIVATION_CODE_DISPLAY_PREFIX_LENGTH",
    "DeviceActivationService",
]