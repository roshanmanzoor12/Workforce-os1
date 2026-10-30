from __future__ import annotations


PRIVACY_READ_PERMISSION = "privacy:read"
PRIVACY_MANAGE_PERMISSION = "privacy:manage"


class PrivacyPermissionError(PermissionError):
    pass


def require_privacy_access(
    *,
    can_manage: bool = True,
) -> None:
    if not can_manage:
        raise PrivacyPermissionError(
            "Privacy-management permission is required."
        )