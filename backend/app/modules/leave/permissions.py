from __future__ import annotations


# =========================================================
# LEAVE PERMISSION KEYS
# =========================================================


LEAVE_VIEW = (
    "leave.view"
)

LEAVE_MANAGE = (
    "leave.manage"
)

LEAVE_SELF_READ = (
    "leave.self.read"
)

LEAVE_TEAM_READ = (
    "leave.team.read"
)

LEAVE_ALL_READ = (
    "leave.all.read"
)

LEAVE_APPROVE = (
    "leave.approve"
)

LEAVE_POLICY_MANAGE = (
    "leave.policy.manage"
)

LEAVE_BALANCE_MANAGE = (
    "leave.balance.manage"
)


ALL_LEAVE_PERMISSIONS = frozenset(
    {
        LEAVE_VIEW,
        LEAVE_MANAGE,
        LEAVE_SELF_READ,
        LEAVE_TEAM_READ,
        LEAVE_ALL_READ,
        LEAVE_APPROVE,
        LEAVE_POLICY_MANAGE,
        LEAVE_BALANCE_MANAGE,
    }
)


__all__ = [
    "LEAVE_VIEW",
    "LEAVE_MANAGE",
    "LEAVE_SELF_READ",
    "LEAVE_TEAM_READ",
    "LEAVE_ALL_READ",
    "LEAVE_APPROVE",
    "LEAVE_POLICY_MANAGE",
    "LEAVE_BALANCE_MANAGE",
    "ALL_LEAVE_PERMISSIONS",
]