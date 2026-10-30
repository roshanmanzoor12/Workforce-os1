from __future__ import annotations


PLATFORM_ADMIN_PERMISSION = "platform_admin:manage"


class PlatformAdminPermissionError(PermissionError):
    """Raised when a platform-admin operation is not authorized."""


def require_platform_admin(is_platform_admin: bool = True) -> None:
    """
    Temporary contract guard.

    Replace the boolean source with the authenticated user's
    platform-admin claim when the control-plane identity layer is wired.
    """
    if not is_platform_admin:
        raise PlatformAdminPermissionError(
            "Platform-admin permission is required."
        )