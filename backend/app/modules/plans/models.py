from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class Plan:
    id: UUID = field(default_factory=uuid4)
    code: str = ""
    name: str = ""
    description: str | None = None
    monthly_price_cents: int = 0
    features: dict[str, Any] = field(default_factory=dict)
    limits: dict[str, int | float | None] = field(default_factory=dict)
    is_active: bool = True
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)