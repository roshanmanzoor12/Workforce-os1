from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class PrivacyPolicy:
    id: UUID
    workspace_id: UUID
    name: str
    description: str | None = None
    is_active: bool = True
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)


@dataclass(slots=True)
class PrivacyZone:
    id: UUID
    workspace_id: UUID
    name: str
    zone_type: str
    value: str
    is_active: bool = True
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)


@dataclass(slots=True)
class PrivacyExclusion:
    id: UUID
    workspace_id: UUID
    exclusion_type: str
    value: str
    reason: str | None = None
    is_active: bool = True
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)