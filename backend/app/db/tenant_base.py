from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, MetaData
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
)


# =========================================================
# NAMING CONVENTION
# =========================================================

TENANT_NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


tenant_metadata = MetaData(
    naming_convention=TENANT_NAMING_CONVENTION
)


# =========================================================
# TENANT DECLARATIVE BASE
# =========================================================


class TenantBase(DeclarativeBase):
    """
    Shared SQLAlchemy declarative base for tenant databases.

    This metadata registry is deliberately separate from the
    WorkforceOS control-plane Base metadata.

    Control-plane tables include objects such as:

        users
        auth_identities
        refresh_sessions
        workspaces
        workspace_memberships
        tenant_database_registry

    Tenant databases must not inherit or recreate those control
    tables.

    Every tenant-specific ORM model should inherit from TenantBase
    directly or through TenantStandardModelMixin.
    """

    metadata = tenant_metadata


# =========================================================
# UUID PRIMARY KEY MIXIN
# =========================================================


class TenantUUIDPrimaryKeyMixin:
    """
    Adds a UUID primary key to tenant models.

    UUID values are generated in Python so behavior stays
    consistent across PostgreSQL, tests, and migrations.
    """

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )


# =========================================================
# TIMESTAMP MIXIN
# =========================================================


class TenantTimestampMixin:
    """
    Standard UTC timestamps for tenant models.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(
            timezone.utc
        ),
        nullable=False,
        index=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(
            timezone.utc
        ),
        onupdate=lambda: datetime.now(
            timezone.utc
        ),
        nullable=False,
    )


# =========================================================
# SOFT DELETE MIXIN
# =========================================================


class TenantSoftDeleteMixin:
    """
    Optional soft-delete behavior for tenant records.

    Use only for tenant entities where historical preservation
    is required.
    """

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        self.deleted_at = datetime.now(
            timezone.utc
        )

    def restore(self) -> None:
        self.deleted_at = None


# =========================================================
# STANDARD TENANT MODEL MIXIN
# =========================================================


class TenantStandardModelMixin(
    TenantUUIDPrimaryKeyMixin,
    TenantTimestampMixin,
):
    """
    Common mixin for normal tenant database tables.

    Example:

        class Employee(
            TenantStandardModelMixin,
            TenantBase,
        ):
            __tablename__ = "employees"
    """

    pass


# =========================================================
# SERIALIZATION HELPER
# =========================================================


class TenantModelSerializerMixin:
    """
    Convenience serializer for internal tenant tooling.

    Do not use this as a public API serializer.

    Public API responses should continue to use explicit
    Pydantic schemas.
    """

    def to_dict(
        self,
        *,
        exclude: set[str] | None = None,
    ) -> dict[str, Any]:
        excluded = exclude or set()

        result: dict[str, Any] = {}

        for column in self.__table__.columns:
            name = column.name

            if name in excluded:
                continue

            value = getattr(
                self,
                name,
            )

            if isinstance(
                value,
                uuid.UUID,
            ):
                value = str(
                    value
                )

            elif isinstance(
                value,
                datetime,
            ):
                value = value.isoformat()

            result[
                name
            ] = value

        return result


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "TENANT_NAMING_CONVENTION",
    "tenant_metadata",
    "TenantBase",
    "TenantUUIDPrimaryKeyMixin",
    "TenantTimestampMixin",
    "TenantSoftDeleteMixin",
    "TenantStandardModelMixin",
    "TenantModelSerializerMixin",
]