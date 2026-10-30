from __future__ import annotations

from typing import Any


class WorkforceError(Exception):
    """
    Base exception for all expected WorkforceOS application errors.

    These exceptions should be converted into consistent HTTP responses
    by the global exception handler/middleware.
    """

    status_code: int = 500
    code: str = "WORKFORCE_ERROR"
    default_message: str = "An unexpected WorkforceOS error occurred."

    def __init__(
        self,
        message: str | None = None,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message or self.default_message
        self.details = details or {}

        super().__init__(self.message)


# =========================================================
# CONFIGURATION
# =========================================================


class ConfigurationError(WorkforceError):
    status_code = 500
    code = "CONFIGURATION_ERROR"
    default_message = "Application configuration is invalid."


# =========================================================
# DATABASE / INFRASTRUCTURE
# =========================================================


class DatabaseError(WorkforceError):
    status_code = 503
    code = "DATABASE_ERROR"
    default_message = "Database service is unavailable."


class RedisError(WorkforceError):
    status_code = 503
    code = "REDIS_ERROR"
    default_message = "Redis service is unavailable."


class StorageError(WorkforceError):
    status_code = 503
    code = "STORAGE_ERROR"
    default_message = "Object storage service is unavailable."


class ExternalServiceError(WorkforceError):
    status_code = 502
    code = "EXTERNAL_SERVICE_ERROR"
    default_message = "An external service request failed."


# =========================================================
# AUTHENTICATION
# =========================================================


class AuthenticationError(WorkforceError):
    status_code = 401
    code = "AUTHENTICATION_ERROR"
    default_message = "Authentication failed."


class InvalidCredentials(AuthenticationError):
    code = "INVALID_CREDENTIALS"
    default_message = "Invalid email or password."


class InvalidToken(AuthenticationError):
    code = "INVALID_TOKEN"
    default_message = "Authentication token is invalid."


class TokenExpired(AuthenticationError):
    code = "TOKEN_EXPIRED"
    default_message = "Authentication token has expired."


class SessionExpired(AuthenticationError):
    code = "SESSION_EXPIRED"
    default_message = "Your session has expired."


class AccountLocked(AuthenticationError):
    code = "ACCOUNT_LOCKED"
    default_message = "This account is locked."


class AccountDisabled(AuthenticationError):
    code = "ACCOUNT_DISABLED"
    default_message = "This account is disabled."


class EmailNotVerified(AuthenticationError):
    code = "EMAIL_NOT_VERIFIED"
    default_message = "Email verification is required."


# =========================================================
# AUTHORIZATION / RBAC
# =========================================================


class PermissionDenied(WorkforceError):
    status_code = 403
    code = "PERMISSION_DENIED"
    default_message = "You do not have permission to perform this action."


class RoleRequired(PermissionDenied):
    code = "ROLE_REQUIRED"
    default_message = "The required role is not assigned."


class FeatureNotAllowed(PermissionDenied):
    code = "FEATURE_NOT_ALLOWED"
    default_message = "This feature is not available for the current account."


# =========================================================
# WORKSPACE / MEMBERSHIP / TENANT
# =========================================================


class WorkspaceNotFound(WorkforceError):
    status_code = 404
    code = "WORKSPACE_NOT_FOUND"
    default_message = "Workspace was not found."


class MembershipNotFound(WorkforceError):
    status_code = 404
    code = "MEMBERSHIP_NOT_FOUND"
    default_message = "Workspace membership was not found."


class MembershipDenied(PermissionDenied):
    code = "MEMBERSHIP_DENIED"
    default_message = "You do not have access to this workspace."


class TenantNotFound(WorkforceError):
    status_code = 404
    code = "TENANT_NOT_FOUND"
    default_message = "Tenant database was not found."


class TenantProvisioningError(WorkforceError):
    status_code = 500
    code = "TENANT_PROVISIONING_ERROR"
    default_message = "Tenant provisioning failed."


class TenantIsolationError(WorkforceError):
    status_code = 403
    code = "TENANT_ISOLATION_ERROR"
    default_message = "Tenant isolation policy blocked this request."


# =========================================================
# RESOURCE / BUSINESS ERRORS
# =========================================================


class ResourceNotFound(WorkforceError):
    status_code = 404
    code = "RESOURCE_NOT_FOUND"
    default_message = "Requested resource was not found."


class ConflictError(WorkforceError):
    status_code = 409
    code = "CONFLICT"
    default_message = "The requested operation conflicts with existing data."


class DuplicateResource(ConflictError):
    code = "DUPLICATE_RESOURCE"
    default_message = "A matching resource already exists."


class InvalidState(ConflictError):
    code = "INVALID_STATE"
    default_message = "The resource is not in a valid state for this operation."


# =========================================================
# VALIDATION
# =========================================================


class ValidationError(WorkforceError):
    status_code = 422
    code = "VALIDATION_ERROR"
    default_message = "Request validation failed."


class BadRequestError(WorkforceError):
    status_code = 400
    code = "BAD_REQUEST"
    default_message = "The request is invalid."


# =========================================================
# RATE LIMIT
# =========================================================


class RateLimitExceeded(WorkforceError):
    status_code = 429
    code = "RATE_LIMIT_EXCEEDED"
    default_message = "Too many requests. Please try again later."


# =========================================================
# BILLING / SUBSCRIPTION
# =========================================================


class SubscriptionRequired(PermissionDenied):
    code = "SUBSCRIPTION_REQUIRED"
    default_message = "An active subscription is required."


class SubscriptionLimitExceeded(WorkforceError):
    status_code = 409
    code = "SUBSCRIPTION_LIMIT_EXCEEDED"
    default_message = "The subscription limit has been reached."


class PaymentRequired(WorkforceError):
    status_code = 402
    code = "PAYMENT_REQUIRED"
    default_message = "Payment is required to continue."


class PaymentFailed(WorkforceError):
    status_code = 402
    code = "PAYMENT_FAILED"
    default_message = "Payment processing failed."


# =========================================================
# FILE / MEDIA
# =========================================================


class FileTooLarge(WorkforceError):
    status_code = 413
    code = "FILE_TOO_LARGE"
    default_message = "The uploaded file is too large."


class UnsupportedFileType(WorkforceError):
    status_code = 415
    code = "UNSUPPORTED_FILE_TYPE"
    default_message = "This file type is not supported."


# =========================================================
# MONITORING
# =========================================================


class MonitoringPolicyDenied(PermissionDenied):
    code = "MONITORING_POLICY_DENIED"
    default_message = "Monitoring policy does not allow this operation."


class DeviceNotRegistered(WorkforceError):
    status_code = 404
    code = "DEVICE_NOT_REGISTERED"
    default_message = "The employee device is not registered."


# =========================================================
# HELPERS
# =========================================================


def error_payload(
    exc: WorkforceError,
    *,
    request_id: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "error": {
            "code": exc.code,
            "message": exc.message,
        }
    }

    if exc.details:
        payload["error"]["details"] = exc.details

    if request_id:
        payload["error"]["request_id"] = request_id

    return payload