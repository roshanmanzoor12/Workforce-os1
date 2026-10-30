from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, MetaData
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


# =========================================================
# NAMING CONVENTION
# =========================================================

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


metadata = MetaData(
    naming_convention=NAMING_CONVENTION
)


# =========================================================
# DECLARATIVE BASE
# =========================================================

class Base(DeclarativeBase):
    """
    Shared SQLAlchemy base class for all WorkforceOS ORM models.

    Every control-plane and tenant ORM model should inherit from this
    base unless a deliberately separate metadata registry is required.
    """

    metadata = metadata


# =========================================================
# UUID MIXIN
# =========================================================

class UUIDPrimaryKeyMixin:
    """
    Adds UUID primary key support.

    UUIDs are generated in Python so they work consistently across:
    - PostgreSQL
    - tests
    - migration environments
    """

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )


# =========================================================
# TIMESTAMP MIXIN
# =========================================================

class TimestampMixin:
    """
    Adds standard created_at / updated_at timestamps.

    All timestamps are timezone-aware and stored in UTC.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


# =========================================================
# SOFT DELETE MIXIN
# =========================================================

class SoftDeleteMixin:
    """
    Optional soft-delete fields.

    Use this only on entities where historical preservation is required.
    Do not automatically add it to every table.
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
        self.deleted_at = datetime.now(timezone.utc)

    def restore(self) -> None:
        self.deleted_at = None


# =========================================================
# STANDARD MODEL MIXIN
# =========================================================

class StandardModelMixin(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
):
    """
    Common mixin for normal WorkforceOS tables.

    Example:

        class User(StandardModelMixin, Base):
            __tablename__ = "users"
    """

    pass


# =========================================================
# SERIALIZATION HELPER
# =========================================================

class ModelSerializerMixin:
    """
    Convenience helper for debugging, logging, and internal tooling.

    Do not use this as the public API serializer.
    Public API responses should use Pydantic schemas.
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

            value = getattr(self, name)

            if isinstance(value, uuid.UUID):
                value = str(value)

            elif isinstance(value, datetime):
                value = value.isoformat()

            result[name] = value

        return result