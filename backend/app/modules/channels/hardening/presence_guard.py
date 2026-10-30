from __future__ import annotations

from dataclasses import dataclass
from datetime import (
    datetime,
    timedelta,
    timezone,
)


def utcnow() -> datetime:
    return datetime.now(
        timezone.utc
    )


@dataclass(
    frozen=True,
    slots=True,
)
class PresenceEvaluation:
    status: str

    age_seconds: float

    online: bool
    idle: bool
    stale: bool


class PresenceLifetimeGuard:
    """
    Consistent presence and typing lifetime policy.

    Redis TTL remains the source of automatic cleanup.  This helper keeps
    the application-side interpretation deterministic across HTTP,
    websocket and tests.
    """

    def __init__(
        self,
        *,
        online_ttl_seconds: int = 90,
        idle_after_seconds: int = 60,
        typing_ttl_seconds: int = 8,
    ) -> None:
        if online_ttl_seconds <= 0:
            raise ValueError(
                "online_ttl_seconds must be positive."
            )

        if idle_after_seconds <= 0:
            raise ValueError(
                "idle_after_seconds must be positive."
            )

        if idle_after_seconds >= online_ttl_seconds:
            raise ValueError(
                "idle_after_seconds must be less than "
                "online_ttl_seconds."
            )

        if typing_ttl_seconds <= 0:
            raise ValueError(
                "typing_ttl_seconds must be positive."
            )

        self.online_ttl_seconds = (
            online_ttl_seconds
        )

        self.idle_after_seconds = (
            idle_after_seconds
        )

        self.typing_ttl_seconds = (
            typing_ttl_seconds
        )

    @staticmethod
    def _ensure_aware(
        value: datetime,
    ) -> datetime:
        if value.tzinfo is None:
            return value.replace(
                tzinfo=timezone.utc
            )

        return value.astimezone(
            timezone.utc
        )

    def evaluate(
        self,
        *,
        last_seen_at: datetime,
        now: datetime | None = None,
    ) -> PresenceEvaluation:
        current = (
            self._ensure_aware(
                now
            )
            if now is not None
            else utcnow()
        )

        last_seen = (
            self._ensure_aware(
                last_seen_at
            )
        )

        age = max(
            (
                current -
                last_seen
            ).total_seconds(),
            0.0,
        )

        if (
            age >=
            self.online_ttl_seconds
        ):
            return PresenceEvaluation(
                status="offline",
                age_seconds=age,
                online=False,
                idle=False,
                stale=True,
            )

        if (
            age >=
            self.idle_after_seconds
        ):
            return PresenceEvaluation(
                status="idle",
                age_seconds=age,
                online=True,
                idle=True,
                stale=False,
            )

        return PresenceEvaluation(
            status="online",
            age_seconds=age,
            online=True,
            idle=False,
            stale=False,
        )

    def presence_expiry_at(
        self,
        *,
        touched_at: datetime | None = None,
    ) -> datetime:
        base = (
            self._ensure_aware(
                touched_at
            )
            if touched_at is not None
            else utcnow()
        )

        return (
            base +
            timedelta(
                seconds=(
                    self.online_ttl_seconds
                )
            )
        )

    def typing_expiry_at(
        self,
        *,
        touched_at: datetime | None = None,
    ) -> datetime:
        base = (
            self._ensure_aware(
                touched_at
            )
            if touched_at is not None
            else utcnow()
        )

        return (
            base +
            timedelta(
                seconds=(
                    self.typing_ttl_seconds
                )
            )
        )

    def typing_is_active(
        self,
        *,
        typing_started_at: datetime,
        now: datetime | None = None,
    ) -> bool:
        current = (
            self._ensure_aware(
                now
            )
            if now is not None
            else utcnow()
        )

        started = (
            self._ensure_aware(
                typing_started_at
            )
        )

        age = (
            current -
            started
        ).total_seconds()

        return (
            0 <=
            age <
            self.typing_ttl_seconds
        )