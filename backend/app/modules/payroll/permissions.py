from __future__ import annotations


PAYROLL_VIEW = (
    "payroll.view"
)

PAYROLL_SELF_READ = (
    "payroll.self.read"
)

PAYROLL_TEAM_READ = (
    "payroll.team.read"
)

PAYROLL_ALL_READ = (
    "payroll.all.read"
)

PAYROLL_RUN = (
    "payroll.run"
)

PAYROLL_EDIT = (
    "payroll.edit"
)

PAYROLL_APPROVE = (
    "payroll.approve"
)

PAYROLL_LOCK = (
    "payroll.lock"
)

PAYROLL_MARK_PAID = (
    "payroll.mark_paid"
)

PAYROLL_EXPORT = (
    "payroll.export"
)

COMPENSATION_VIEW = (
    "compensation.view"
)

COMPENSATION_MANAGE = (
    "compensation.manage"
)


ALL_PAYROLL_PERMISSIONS = frozenset(
    {
        PAYROLL_VIEW,
        PAYROLL_SELF_READ,
        PAYROLL_TEAM_READ,
        PAYROLL_ALL_READ,
        PAYROLL_RUN,
        PAYROLL_EDIT,
        PAYROLL_APPROVE,
        PAYROLL_LOCK,
        PAYROLL_MARK_PAID,
        PAYROLL_EXPORT,
        COMPENSATION_VIEW,
        COMPENSATION_MANAGE,
    }
)


__all__ = [
    "PAYROLL_VIEW",
    "PAYROLL_SELF_READ",
    "PAYROLL_TEAM_READ",
    "PAYROLL_ALL_READ",
    "PAYROLL_RUN",
    "PAYROLL_EDIT",
    "PAYROLL_APPROVE",
    "PAYROLL_LOCK",
    "PAYROLL_MARK_PAID",
    "PAYROLL_EXPORT",
    "COMPENSATION_VIEW",
    "COMPENSATION_MANAGE",
    "ALL_PAYROLL_PERMISSIONS",
]