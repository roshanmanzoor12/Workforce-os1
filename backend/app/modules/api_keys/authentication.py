from __future__ import annotations

import hashlib
import hmac
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFound
from app.db.tenant_context import (
    AuthorizedTenantContext,
    resolve_authorized_tenant_context,
    verify_tenant_identity,
)
from app.modules.api_keys.models import WorkspaceAPIKey
from app.modules.auth.models import User
from app.modules.workspace_permissions.service import (
    WorkspacePermissionService,
)


SUPPORTED_SCOPES = frozenset(
    {
        "employees.read",
        "reports.self.read",
        "analytics.self.read",
    }
)

KEY_PATTERN = re.compile(
    r"(wfos_[0-9a-f]{32})\.([A-Za-z0-9_-]{43})"
)


def authentication_error() -> HTTPException:
    return HTTPException(
        status_code=401,
        detail="Invalid or unavailable API key.",
        headers={"WWW-Authenticate": "ApiKey"},
    )


def parse_api_key(secret: str | None) -> tuple[str, str]:
    if not isinstance(secret, str):
        raise authentication_error()

    match = KEY_PATTERN.fullmatch(secret)

    if match is None:
        raise authentication_error()

    prefix = match.group(1)
    digest = hashlib.sha256(secret.encode("utf-8")).hexdigest()

    return prefix, digest


@dataclass(frozen=True, slots=True)
class APIKeyPrincipal:
    key_id: UUID
    workspace_id: UUID
    user_id: UUID
    membership_id: UUID
    scopes: frozenset[str]

    def require(self, permission: str) -> None:
        if permission not in self.scopes:
            raise HTTPException(
                status_code=403,
                detail="API key scope is insufficient.",
            )


class APIKeyAuthentication:
    """
    Authenticate against an already identity-verified tenant session.

    This service owns its tenant transaction. Do not call it after
    making unrelated changes in the same session.
    """

    def __init__(
        self,
        *,
        tenant_session: AsyncSession,
        control_session: AsyncSession,
        workspace_id: UUID,
        database_name: str,
        cluster_key: str,
    ) -> None:
        self.tenant_session = tenant_session
        self.control_session = control_session
        self.workspace_id = workspace_id
        self.database_name = database_name
        self.cluster_key = cluster_key

    async def _load_key(
        self,
        prefix: str,
    ) -> WorkspaceAPIKey | None:
        result = await self.tenant_session.execute(
            select(WorkspaceAPIKey)
            .where(
                WorkspaceAPIKey.workspace_id == self.workspace_id,
                WorkspaceAPIKey.key_prefix == prefix,
            )
            .limit(2)
            .with_for_update()
        )

        rows = list(result.scalars().all())

        # Ambiguous prefixes fail closed.
        return rows[0] if len(rows) == 1 else None

    async def _creator_context(
        self,
        user_id: UUID,
    ) -> AuthorizedTenantContext:
        result = await self.control_session.execute(
            select(User).where(User.id == user_id)
        )

        user = result.scalar_one_or_none()

        if (
            user is None
            or not user.is_active
            or user.is_locked
            or not user.is_email_verified
        ):
            raise authentication_error()

        try:
            context = await resolve_authorized_tenant_context(
                self.control_session,
                workspace_id=self.workspace_id,
                user_id=user_id,
            )
        except ResourceNotFound:
            raise authentication_error() from None

        if (
            context.workspace_id != self.workspace_id
            or context.database_name != self.database_name
            or context.cluster_key != self.cluster_key
        ):
            raise authentication_error()

        await verify_tenant_identity(
            self.tenant_session,
            context=context,
        )

        return context

    async def authenticate(
        self,
        secret: str | None,
        *,
        required_scopes: frozenset[str] = frozenset(),
    ) -> APIKeyPrincipal:
        try:
            prefix, digest = parse_api_key(secret)
            key = await self._load_key(prefix)

            stored_digest = key.secret_hash if key is not None else "0" * 64

            valid_digest = hmac.compare_digest(
                digest,
                stored_digest,
            )

            if (
                key is None
                or not valid_digest
                or key.workspace_id != self.workspace_id
                or key.revoked_at is not None
            ):
                raise authentication_error()

            now = datetime.now(timezone.utc)

            if key.expires_at is not None:
                if (
                    key.expires_at.tzinfo is None
                    or key.expires_at.utcoffset() is None
                    or key.expires_at <= now
                ):
                    raise authentication_error()

            if (
                not isinstance(key.scopes, list)
                or not key.scopes
                or not all(isinstance(item, str) for item in key.scopes)
            ):
                raise authentication_error()

            saved_scopes = frozenset(key.scopes)

            if not saved_scopes.issubset(SUPPORTED_SCOPES):
                raise authentication_error()

            context = await self._creator_context(
                key.created_by_user_id
            )

            permissions = WorkspacePermissionService(context)

            effective_scopes = frozenset(
                permission
                for permission in saved_scopes
                if permissions.has(permission)
            )

            if (
                not effective_scopes
                or not required_scopes.issubset(effective_scopes)
            ):
                raise HTTPException(
                    status_code=403,
                    detail="API key scope is insufficient.",
                )

            principal = APIKeyPrincipal(
                key_id=key.id,
                workspace_id=self.workspace_id,
                user_id=context.user_id,
                membership_id=context.membership_id,
                scopes=effective_scopes,
            )

            key.last_used_at = now

            await self.tenant_session.flush()
            await self.tenant_session.commit()

            return principal

        except BaseException:
            try:
                await self.tenant_session.rollback()
            except BaseException:
                pass
            raise