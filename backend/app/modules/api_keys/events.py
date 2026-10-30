from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID


@dataclass(frozen=True, slots=True)
class APIKeyChanged:
    workspace_id: UUID
    key_id: UUID
    actor_user_id: UUID
    action: Literal["created", "revoked", "rotated"]
    occurred_at: datetime


# Event payload contract only.
# Publishing to the existing audit/event system is not wired yet.
# Never include a secret or secret hash in an event.