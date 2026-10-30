from enum import StrEnum


class BillingProvider(StrEnum):
    NONE = "none"
    STRIPE = "stripe"


class SubscriptionStatus(StrEnum):
    NONE = "none"
    TRIALING = "trialing"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    UNPAID = "unpaid"


class EntitlementCode(StrEnum):
    CREATE_WORKSPACE = "create_workspace"
    MONITORING = "monitoring"
    LIVE_SCREEN = "live_screen"
    ADVANCED_ANALYTICS = "advanced_analytics"