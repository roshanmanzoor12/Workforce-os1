from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.tenant_base import TenantBase, TenantStandardModelMixin


class MonitoringConsent(TenantStandardModelMixin, TenantBase):
    __tablename__ = "monitoring_consents"
    __table_args__ = (UniqueConstraint("user_id", name="uq_monitoring_consents_user"),)

    user_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    granted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    policy_version: Mapped[str] = mapped_column(String(64), nullable=False, default="v1")
    granted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class MonitoringEvent(TenantStandardModelMixin, TenantBase):
    __tablename__ = "monitoring_events"
    __table_args__ = (
        Index("ix_monitoring_events_kind_created", "kind", "created_at"),
        Index("ix_monitoring_events_device_created", "device_id", "created_at"),
    )

    kind: Mapped[str] = mapped_column(String(48), nullable=False)
    device_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    employee_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="agent")


class MonitoringLiveSession(TenantStandardModelMixin, TenantBase):
    __tablename__ = "monitoring_live_sessions"
    __table_args__ = (Index("ix_monitoring_live_sessions_status", "status"),)

    device_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    requested_by_user_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="requested")
    consent_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
