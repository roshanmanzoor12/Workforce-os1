from __future__ import annotations


RULES_READ_PERMISSION = "rules:read"
RULES_MANAGE_PERMISSION = "rules:manage"


class RulesPermissionError(PermissionError):
    pass


def require_rules_access(
    *,
    can_manage: bool = True,
) -> None:
    if not can_manage:
        raise RulesPermissionError(
            "Rules-management permission is required."
        )