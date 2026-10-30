"""
WorkforceOS channel realtime production-hardening primitives.

Phase 17 keeps hardening concerns isolated from the already-working
Phase 16C realtime public API.  The modules in this package are wired
into the existing channel realtime stack incrementally.

Public responsibilities:

- centralized hardening configuration;
- atomic one-use realtime ticket consumption;
- channel membership/access revalidation;
- Redis-backed rate limiting;
- presence/typing lifetime guards;
- durable read-state UPSERT helpers;
- structured realtime observability;
- attachment channel-access validation.
"""

from app.modules.channels.hardening.access import (
    ChannelAccessContext,
    ChannelAccessDenied,
    ChannelAccessGuard,
)
from app.modules.channels.hardening.attachment_access import (
    ChannelAttachmentAccessGuard,
)
from app.modules.channels.hardening.config import (
    ChannelHardeningSettings,
    get_channel_hardening_settings,
)
from app.modules.channels.hardening.observability import (
    ChannelRealtimeMetrics,
    channel_realtime_metrics,
)
from app.modules.channels.hardening.presence_guard import (
    PresenceLifetimeGuard,
)
from app.modules.channels.hardening.rate_limit import (
    ChannelRateLimitDecision,
    ChannelRateLimiter,
)
from app.modules.channels.hardening.read_state_upsert import (
    ChannelReadStateUpserter,
)
from app.modules.channels.hardening.ticket_store import (
    AtomicRealtimeTicketStore,
    TicketConsumeResult,
)

__all__ = [
    "AtomicRealtimeTicketStore",
    "ChannelAccessContext",
    "ChannelAccessDenied",
    "ChannelAccessGuard",
    "ChannelAttachmentAccessGuard",
    "ChannelHardeningSettings",
    "ChannelRateLimitDecision",
    "ChannelRateLimiter",
    "ChannelReadStateUpserter",
    "ChannelRealtimeMetrics",
    "PresenceLifetimeGuard",
    "TicketConsumeResult",
    "channel_realtime_metrics",
    "get_channel_hardening_settings",
]