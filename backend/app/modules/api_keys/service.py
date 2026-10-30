from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import HTTPException
from pydantic import SecretStr

from app.db.tenant_dependency import TenantRequestScope
from app.modules.api_keys.audit_repository import APIKeyAuditRepository
from app.modules.api_keys.models import WorkspaceAPIKey
from app.modules.api_keys.permissions import (
    require_api_key_management,
    require_grantable_scopes,
)
from app.modules.api_keys.repository import APIKeyRepository
from app.modules.api_keys.schemas import (
    APIKeyCreate,
    APIKeyIssued,
    APIKeyPublic,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def hash_secret(secret: str) -> str:
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


def generate_secret(key_id: UUID) -> tuple[str, str]:
    prefix = f"wfos_{key_id.hex}"
    return prefix, f"{prefix}.{secrets.token_urlsafe(32)}"


class APIKeyService:
    def __init__(self, scope: TenantRequestScope) -> None:
        self.scope = scope
        self.repository = APIKeyRepository(
            scope.session,
            scope.workspace_id,
        )
        self.audit_repository = APIKeyAuditRepository(
            scope.session,
            scope.workspace_id,
        )

    def _authorize(self) -> None:
        require_api_key_management(self.scope)

    async def list_keys(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[APIKeyPublic]:
        self._authorize()
        rows = await self.repository.list(
            limit=limit,
            offset=offset,
        )
        return [APIKeyPublic.model_validate(row) for row in rows]

    async def get_key(self, key_id: UUID) -> APIKeyPublic:
        self._authorize()
        return APIKeyPublic.model_validate(await self._get(key_id))

    async def _get(
        self,
        key_id: UUID,
        *,
        for_update: bool = False,
    ) -> WorkspaceAPIKey:
        row = await self.repository.get(
            key_id,
            for_update=for_update,
        )
        if row is None:
            raise HTTPException(
                status_code=404,
                detail="API key not found.",
            )
        return row

    def _build_key(
        self,
        *,
        name: str,
        scopes: list[str],
        expires_at: datetime | None,
    ) -> tuple[WorkspaceAPIKey, str]:
        key_id = uuid4()
        prefix, secret = generate_secret(key_id)
        now = utc_now()

        row = WorkspaceAPIKey(
            id=key_id,
            workspace_id=self.scope.workspace_id,
            created_by_user_id=self.scope.user_id,
            name=name,
            key_prefix=prefix,
            secret_hash=hash_secret(secret),
            scopes=list(scopes),
            expires_at=expires_at,
            revoked_at=None,
            revoked_by_user_id=None,
            last_used_at=None,
            created_at=now,
            updated_at=now,
        )
        return row, secret

    async def create_key(
        self,
        payload: APIKeyCreate,
    ) -> APIKeyIssued:
        self._authorize()
        require_grantable_scopes(self.scope, payload.scopes)

        if (
            payload.expires_at is not None
            and payload.expires_at <= utc_now()
        ):
            raise HTTPException(
                status_code=422,
                detail="Expiry must be in the future.",
            )

        row, secret = self._build_key(
            name=payload.name,
            scopes=payload.scopes,
            expires_at=payload.expires_at,
        )

        try:
            await self.repository.add(row)
            self.audit_repository.enqueue(
                actor_user_id=self.scope.user_id,
                key_id=row.id,
                action="created",
                occurred_at=row.created_at,
            )
            await self.scope.session.flush()
            public = APIKeyPublic.model_validate(row)
            await self.scope.session.commit()
        except Exception:
            await self.scope.session.rollback()
            raise

        return APIKeyIssued(
            key=public,
            secret=SecretStr(secret),
        )

    async def revoke_key(self, key_id: UUID) -> APIKeyPublic:
        self._authorize()

        try:
            row = await self._get(key_id, for_update=True)

            if row.revoked_at is None:
                now = utc_now()
                row.revoked_at = now
                row.revoked_by_user_id = self.scope.user_id
                row.updated_at = now

                self.audit_repository.enqueue(
                    actor_user_id=self.scope.user_id,
                    key_id=row.id,
                    action="revoked",
                    occurred_at=now,
                )

            await self.scope.session.flush()
            public = APIKeyPublic.model_validate(row)
            await self.scope.session.commit()
        except Exception:
            await self.scope.session.rollback()
            raise

        return public

    async def rotate_key(self, key_id: UUID) -> APIKeyIssued:
        self._authorize()

        try:
            old = await self._get(key_id, for_update=True)
            now = utc_now()

            if old.revoked_at is not None:
                raise HTTPException(
                    status_code=409,
                    detail="Revoked API keys cannot be rotated.",
                )

            if old.expires_at is not None and old.expires_at <= now:
                raise HTTPException(
                    status_code=409,
                    detail="Expired API keys cannot be rotated.",
                )

            require_grantable_scopes(self.scope, old.scopes)

            replacement, secret = self._build_key(
                name=old.name,
                scopes=old.scopes,
                expires_at=old.expires_at,
            )

            old.revoked_at = now
            old.revoked_by_user_id = self.scope.user_id
            old.updated_at = now

            await self.repository.add(replacement)

            self.audit_repository.enqueue(
                actor_user_id=self.scope.user_id,
                key_id=old.id,
                action="rotated",
                occurred_at=now,
                replacement_key_id=replacement.id,
            )

            await self.scope.session.flush()
            public = APIKeyPublic.model_validate(replacement)
            await self.scope.session.commit()
        except Exception:
            await self.scope.session.rollback()
            raise

        return APIKeyIssued(
            key=public,
            secret=SecretStr(secret),
        )