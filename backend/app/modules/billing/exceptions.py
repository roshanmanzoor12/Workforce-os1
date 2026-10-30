class BillingError(Exception):
    pass


class WorkspaceEntitlementDeniedError(
    BillingError
):
    pass


class SubscriptionUnavailableError(
    BillingError
):
    pass