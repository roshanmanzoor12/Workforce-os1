from __future__ import annotations

from app.modules.workspace_permissions.permissions import (
    ALL_WORKSPACE_PERMISSIONS,
    WorkspacePermission,
)


# =========================================================
# BUILT-IN ROLE KEYS
# =========================================================


OWNER_ROLE = "owner"
ADMIN_ROLE = "admin"
MANAGER_ROLE = "manager"
MEMBER_ROLE = "member"
CLIENT_ROLE = "client"

# Compatibility names used by earlier callers and tests.
WORKSPACE_ROLE_OWNER = OWNER_ROLE
WORKSPACE_ROLE_ADMIN = ADMIN_ROLE
WORKSPACE_ROLE_MANAGER = MANAGER_ROLE
WORKSPACE_ROLE_MEMBER = MEMBER_ROLE
WORKSPACE_ROLE_CLIENT = CLIENT_ROLE

BUILT_IN_ROLE_KEYS = frozenset(
    {
        OWNER_ROLE,
        ADMIN_ROLE,
        MANAGER_ROLE,
        MEMBER_ROLE,
        CLIENT_ROLE,
    }
)


ROLE_DISPLAY_NAMES = {
    OWNER_ROLE: "Owner",
    ADMIN_ROLE: "Admin",
    MANAGER_ROLE: "Manager",
    MEMBER_ROLE: "Member",
    CLIENT_ROLE: "Client",
}


# =========================================================
# OWNER
# =========================================================

# Owner always receives every registered permission.
#
# New permissions automatically become available to Owner.
# Owner remains immutable at the role-management layer.


OWNER_PERMISSIONS = (
    ALL_WORKSPACE_PERMISSIONS
)


# =========================================================
# ADMIN
# =========================================================


ADMIN_PERMISSIONS = frozenset(
    {
        # -------------------------------------------------
        # Workspace
        # -------------------------------------------------

        WorkspacePermission
        .WORKSPACE_VIEW
        .value,

        WorkspacePermission
        .WORKSPACE_READ
        .value,

        WorkspacePermission
        .WORKSPACE_MANAGE
        .value,

        WorkspacePermission
        .WORKSPACE_SETTINGS_READ
        .value,

        WorkspacePermission
        .WORKSPACE_SETTINGS_MANAGE
        .value,

        WorkspacePermission
        .LEAVE_VIEW
        .value,

        WorkspacePermission
        .LEAVE_SELF_READ
        .value,

        WorkspacePermission
        .LEAVE_TEAM_READ
        .value,

        WorkspacePermission
        .LEAVE_ALL_READ
        .value,

        WorkspacePermission
        .LEAVE_APPROVE
        .value,

        WorkspacePermission
        .LEAVE_BALANCE_MANAGE
        .value,

        WorkspacePermission
        .LEAVE_MANAGE
        .value,

        WorkspacePermission
        .LEAVE_POLICY_MANAGE
        .value,

        # -------------------------------------------------
        # Members
        # -------------------------------------------------

        WorkspacePermission
        .MEMBERS_VIEW
        .value,

        WorkspacePermission
        .MEMBERS_READ
        .value,

        WorkspacePermission
        .MEMBERS_MANAGE
        .value,

        WorkspacePermission
        .MEMBERS_INVITE
        .value,

        WorkspacePermission
        .MEMBERS_UPDATE
        .value,

        WorkspacePermission
        .MEMBERS_REMOVE
        .value,

        WorkspacePermission
        .MEMBERS_KICK
        .value,

        WorkspacePermission
        .MEMBERS_BAN
        .value,

        WorkspacePermission
        .MEMBERS_MUTE
        .value,

        WorkspacePermission
        .MEMBERS_DEAFEN
        .value,

        WorkspacePermission
        .MEMBERS_HIDE
        .value,

        # -------------------------------------------------
        # Roles
        # -------------------------------------------------

        WorkspacePermission
        .ROLES_READ
        .value,

        WorkspacePermission
        .ROLES_ASSIGN
        .value,

        # roles.manage deliberately excluded.

        # -------------------------------------------------
        # Employees
        # -------------------------------------------------

        WorkspacePermission
        .EMPLOYEES_VIEW
        .value,

        WorkspacePermission
        .EMPLOYEES_MANAGE
        .value,

        WorkspacePermission
        .EMPLOYEES_READ
        .value,

        WorkspacePermission
        .EMPLOYEES_SELF_READ
        .value,

        WorkspacePermission
        .EMPLOYEES_TEAM_READ
        .value,

        WorkspacePermission
        .EMPLOYEES_ALL_READ
        .value,

        WorkspacePermission
        .EMPLOYEES_CREATE
        .value,

        WorkspacePermission
        .EMPLOYEES_UPDATE
        .value,

        WorkspacePermission
        .EMPLOYEES_DELETE
        .value,

        # -------------------------------------------------
        # Departments / Teams
        # -------------------------------------------------

        WorkspacePermission
        .DEPARTMENTS_VIEW
        .value,

        WorkspacePermission
        .DEPARTMENTS_READ
        .value,

        WorkspacePermission
        .DEPARTMENTS_MANAGE
        .value,

        WorkspacePermission
        .TEAMS_VIEW
        .value,

        WorkspacePermission
        .TEAMS_READ
        .value,

        WorkspacePermission
        .TEAMS_MANAGE
        .value,

        # -------------------------------------------------
        # Attendance
        # -------------------------------------------------

        WorkspacePermission
        .ATTENDANCE_VIEW
        .value,

        WorkspacePermission
        .ATTENDANCE_MANAGE
        .value,

        WorkspacePermission
        .ATTENDANCE_SELF_READ
        .value,

        WorkspacePermission
        .ATTENDANCE_TEAM_READ
        .value,

        WorkspacePermission
        .ATTENDANCE_ALL_READ
        .value,

        WorkspacePermission
        .ATTENDANCE_APPROVE
        .value,

        # -------------------------------------------------
        # Phase 12.1 — Shifts / Scheduling
        # -------------------------------------------------

        WorkspacePermission
        .SHIFTS_VIEW
        .value,

        WorkspacePermission
        .SHIFTS_MANAGE
        .value,

        WorkspacePermission
        .SHIFTS_SELF_READ
        .value,

        WorkspacePermission
        .SHIFTS_TEAM_READ
        .value,

        WorkspacePermission
        .SHIFTS_ALL_READ
        .value,

        # -------------------------------------------------
        # Phase 12.1 — Holidays
        # -------------------------------------------------

        WorkspacePermission
        .HOLIDAYS_VIEW
        .value,

        WorkspacePermission
        .HOLIDAYS_MANAGE
        .value,

        WorkspacePermission
        .HOLIDAYS_SELF_READ
        .value,

        WorkspacePermission
        .HOLIDAYS_TEAM_READ
        .value,

        WorkspacePermission
        .HOLIDAYS_ALL_READ
        .value,

        # -------------------------------------------------
        # Compensation / Payroll
        # -------------------------------------------------

        WorkspacePermission
        .COMPENSATION_SELF_READ
        .value,

        WorkspacePermission
        .PAYROLL_READ
        .value,

        WorkspacePermission
        .PAYROLL_MANAGE
        .value,

        # -------------------------------------------------
        # Monitoring
        # -------------------------------------------------

        WorkspacePermission
        .MONITORING_VIEW
        .value,

        WorkspacePermission
        .MONITORING_MANAGE
        .value,

        WorkspacePermission
        .MONITORING_SELF_READ
        .value,

        WorkspacePermission
        .MONITORING_TEAM_READ
        .value,

        WorkspacePermission
        .MONITORING_ALL_READ
        .value,

        WorkspacePermission
        .MONITORING_LIVE_VIEW
        .value,

        WorkspacePermission
        .MONITORING_LIVE_SCREEN
        .value,

        WorkspacePermission
        .MONITORING_SETTINGS_MANAGE
        .value,

        # -------------------------------------------------
        # Devices
        # -------------------------------------------------

        WorkspacePermission
        .DEVICES_SELF_READ
        .value,

        WorkspacePermission
        .DEVICES_TEAM_READ
        .value,

        WorkspacePermission
        .DEVICES_ALL_READ
        .value,

        WorkspacePermission
        .DEVICES_MANAGE
        .value,

        # -------------------------------------------------
        # Tasks
        # -------------------------------------------------

        WorkspacePermission
        .TASKS_SELF_READ
        .value,

        WorkspacePermission
        .TASKS_TEAM_READ
        .value,

        WorkspacePermission
        .TASKS_ALL_READ
        .value,

        WorkspacePermission
        .TASKS_CREATE
        .value,

        WorkspacePermission
        .TASKS_ASSIGN_TEAM
        .value,

        WorkspacePermission
        .TASKS_ASSIGN_ALL
        .value,

        WorkspacePermission
        .TASKS_MANAGE
        .value,

        # -------------------------------------------------
        # Meetings
        # -------------------------------------------------

        WorkspacePermission
        .MEETINGS_VIEW
        .value,

        WorkspacePermission
        .MEETINGS_READ
        .value,

        WorkspacePermission
        .MEETINGS_CREATE
        .value,

        WorkspacePermission
        .MEETINGS_MANAGE
        .value,

        WorkspacePermission
        .MEETINGS_INVITE_TEAM
        .value,

        WorkspacePermission
        .MEETINGS_INVITE_ALL
        .value,

        WorkspacePermission
        .MEETINGS_INVITE_EXTERNAL
        .value,

        # -------------------------------------------------
        # Channels
        # -------------------------------------------------

        WorkspacePermission
        .CHANNELS_READ
        .value,

        WorkspacePermission
        .CHANNELS_CREATE
        .value,

        WorkspacePermission
        .CHANNELS_MANAGE
        .value,

        # -------------------------------------------------
        # Goals
        # -------------------------------------------------

        WorkspacePermission
        .GOALS_VIEW
        .value,

        WorkspacePermission
        .GOALS_MANAGE
        .value,

        WorkspacePermission
        .GOALS_SELF
        .value,

        # -------------------------------------------------
        # Notes
        # -------------------------------------------------

        WorkspacePermission
        .NOTES_VIEW
        .value,

        WorkspacePermission
        .NOTES_MANAGE
        .value,

        WorkspacePermission
        .NOTES_SELF
        .value,

        # -------------------------------------------------
        # Knowledge
        # -------------------------------------------------

        WorkspacePermission
        .KNOWLEDGE_VIEW
        .value,

        WorkspacePermission
        .KNOWLEDGE_MANAGE
        .value,

        WorkspacePermission
        .KNOWLEDGE_SELF
        .value,

        # -------------------------------------------------
        # Timeline
        # -------------------------------------------------

        WorkspacePermission
        .TIMELINE_VIEW
        .value,

        WorkspacePermission
        .TIMELINE_SELF
        .value,

        # -------------------------------------------------
        # Reports
        # -------------------------------------------------

        WorkspacePermission
        .REPORTS_VIEW
        .value,

        WorkspacePermission
        .REPORTS_SELF_READ
        .value,

        WorkspacePermission
        .REPORTS_TEAM_READ
        .value,

        WorkspacePermission
        .REPORTS_ALL_READ
        .value,

        WorkspacePermission
        .REPORTS_EXPORT
        .value,

        # -------------------------------------------------
        # Analytics
        # -------------------------------------------------

        WorkspacePermission
        .ANALYTICS_SELF_READ
        .value,

        WorkspacePermission
        .ANALYTICS_TEAM_READ
        .value,

        WorkspacePermission
        .ANALYTICS_ALL_READ
        .value,

        WorkspacePermission
        .ANALYTICS_EXPORT
        .value,

        # -------------------------------------------------
        # Productivity Insights
        # -------------------------------------------------

        WorkspacePermission
        .PRODUCTIVITY_INSIGHTS_SELF_READ
        .value,

        WorkspacePermission
        .PRODUCTIVITY_INSIGHTS_TEAM_READ
        .value,

        WorkspacePermission
        .PRODUCTIVITY_INSIGHTS_ALL_READ
        .value,

        WorkspacePermission
        .PRODUCTIVITY_INSIGHTS_EXPORT
        .value,

        # -------------------------------------------------
        # Integrations
        # -------------------------------------------------

        WorkspacePermission
        .INTEGRATIONS_USE
        .value,

        WorkspacePermission
        .INTEGRATIONS_MANAGE
        .value,

        WorkspacePermission
        .INTEGRATIONS_ASSIGN
        .value,

        # -------------------------------------------------
        # Billing
        # -------------------------------------------------

        WorkspacePermission
        .BILLING_READ
        .value,

        # billing.manage deliberately excluded.

        # -------------------------------------------------
        # AI
        # -------------------------------------------------

        WorkspacePermission
        .AI_PRODUCTIVITY_USE
        .value,

        WorkspacePermission
        .AI_PRODUCTIVITY_MANAGE
        .value,

        # -------------------------------------------------
        # Notifications / Audit
        # -------------------------------------------------

        WorkspacePermission
        .NOTIFICATIONS_READ
        .value,

        WorkspacePermission
        .AUDIT_VIEW
        .value,

        WorkspacePermission
        .AUDIT_READ
        .value,
    }
)


# =========================================================
# MANAGER
# =========================================================


MANAGER_PERMISSIONS = frozenset(
    {
        # -------------------------------------------------
        # Workspace
        # -------------------------------------------------

        WorkspacePermission
        .WORKSPACE_VIEW
        .value,

        WorkspacePermission
        .WORKSPACE_READ
        .value,

        WorkspacePermission
        .LEAVE_SELF_READ
        .value,

        WorkspacePermission
        .LEAVE_TEAM_READ
        .value,

        WorkspacePermission
        .LEAVE_APPROVE
        .value,

        # -------------------------------------------------
        # Members
        # -------------------------------------------------

        WorkspacePermission
        .MEMBERS_VIEW
        .value,

        WorkspacePermission
        .MEMBERS_READ
        .value,

        # -------------------------------------------------
        # Roles
        # -------------------------------------------------

        WorkspacePermission
        .ROLES_READ
        .value,

        # -------------------------------------------------
        # Employees
        # -------------------------------------------------

        WorkspacePermission
        .EMPLOYEES_VIEW
        .value,

        WorkspacePermission
        .EMPLOYEES_READ
        .value,

        WorkspacePermission
        .EMPLOYEES_SELF_READ
        .value,

        WorkspacePermission
        .EMPLOYEES_TEAM_READ
        .value,

        # -------------------------------------------------
        # Departments / Teams
        # -------------------------------------------------

        WorkspacePermission
        .DEPARTMENTS_VIEW
        .value,

        WorkspacePermission
        .DEPARTMENTS_READ
        .value,

        WorkspacePermission
        .TEAMS_VIEW
        .value,

        WorkspacePermission
        .TEAMS_READ
        .value,

        # -------------------------------------------------
        # Attendance
        # -------------------------------------------------

        WorkspacePermission
        .ATTENDANCE_VIEW
        .value,

        WorkspacePermission
        .ATTENDANCE_SELF_READ
        .value,

        WorkspacePermission
        .ATTENDANCE_TEAM_READ
        .value,

        WorkspacePermission
        .ATTENDANCE_APPROVE
        .value,

        # -------------------------------------------------
        # Phase 12.1 — Shifts / Scheduling
        # -------------------------------------------------

        WorkspacePermission
        .SHIFTS_VIEW
        .value,

        WorkspacePermission
        .SHIFTS_SELF_READ
        .value,

        WorkspacePermission
        .SHIFTS_TEAM_READ
        .value,

        # Manager does NOT automatically receive:
        #
        # shifts.manage
        # shifts.all.read
        #
        # Those remain explicit grants.

        # -------------------------------------------------
        # Phase 12.1 — Holidays
        # -------------------------------------------------

        WorkspacePermission
        .HOLIDAYS_VIEW
        .value,

        WorkspacePermission
        .HOLIDAYS_SELF_READ
        .value,

        WorkspacePermission
        .HOLIDAYS_TEAM_READ
        .value,

        # -------------------------------------------------
        # Compensation
        # -------------------------------------------------

        WorkspacePermission
        .COMPENSATION_SELF_READ
        .value,

        # -------------------------------------------------
        # Monitoring
        # -------------------------------------------------

        WorkspacePermission
        .MONITORING_VIEW
        .value,

        WorkspacePermission
        .MONITORING_SELF_READ
        .value,

        WorkspacePermission
        .MONITORING_TEAM_READ
        .value,

        # -------------------------------------------------
        # Devices
        # -------------------------------------------------

        WorkspacePermission
        .DEVICES_SELF_READ
        .value,

        WorkspacePermission
        .DEVICES_TEAM_READ
        .value,

        # -------------------------------------------------
        # Tasks
        # -------------------------------------------------

        WorkspacePermission
        .TASKS_SELF_READ
        .value,

        WorkspacePermission
        .TASKS_TEAM_READ
        .value,

        WorkspacePermission
        .TASKS_CREATE
        .value,

        WorkspacePermission
        .TASKS_ASSIGN_TEAM
        .value,

        # -------------------------------------------------
        # Meetings
        # -------------------------------------------------

        WorkspacePermission
        .MEETINGS_VIEW
        .value,

        WorkspacePermission
        .MEETINGS_READ
        .value,

        WorkspacePermission
        .MEETINGS_CREATE
        .value,

        WorkspacePermission
        .MEETINGS_INVITE_TEAM
        .value,

        # -------------------------------------------------
        # Channels
        # -------------------------------------------------

        WorkspacePermission
        .CHANNELS_READ
        .value,

        # -------------------------------------------------
        # Goals
        # -------------------------------------------------

        WorkspacePermission
        .GOALS_SELF
        .value,

        WorkspacePermission
        .GOALS_VIEW
        .value,

        # -------------------------------------------------
        # Notes
        # -------------------------------------------------

        WorkspacePermission
        .NOTES_SELF
        .value,

        # -------------------------------------------------
        # Knowledge
        # -------------------------------------------------

        WorkspacePermission
        .KNOWLEDGE_SELF
        .value,

        WorkspacePermission
        .KNOWLEDGE_VIEW
        .value,

        # -------------------------------------------------
        # Timeline
        # -------------------------------------------------

        WorkspacePermission
        .TIMELINE_SELF
        .value,

        WorkspacePermission
        .TIMELINE_VIEW
        .value,

        # -------------------------------------------------
        # Reports
        # -------------------------------------------------

        WorkspacePermission
        .REPORTS_SELF_READ
        .value,

        WorkspacePermission
        .REPORTS_TEAM_READ
        .value,

        # -------------------------------------------------
        # Analytics
        # -------------------------------------------------

        WorkspacePermission
        .ANALYTICS_SELF_READ
        .value,

        WorkspacePermission
        .ANALYTICS_TEAM_READ
        .value,

        # -------------------------------------------------
        # Productivity Insights
        # -------------------------------------------------

        WorkspacePermission
        .PRODUCTIVITY_INSIGHTS_SELF_READ
        .value,

        WorkspacePermission
        .PRODUCTIVITY_INSIGHTS_TEAM_READ
        .value,

        # -------------------------------------------------
        # Integrations
        # -------------------------------------------------

        WorkspacePermission
        .INTEGRATIONS_USE
        .value,

        # -------------------------------------------------
        # AI
        # -------------------------------------------------

        WorkspacePermission
        .AI_PRODUCTIVITY_USE
        .value,

        # -------------------------------------------------
        # Notifications
        # -------------------------------------------------

        WorkspacePermission
        .NOTIFICATIONS_READ
        .value,
    }
)


# =========================================================
# MEMBER
# =========================================================


MEMBER_PERMISSIONS = frozenset(
    {
        # -------------------------------------------------
        # Existing compatibility permissions
        # -------------------------------------------------

        WorkspacePermission
        .WORKSPACE_VIEW
        .value,

        WorkspacePermission
        .MEMBERS_VIEW
        .value,

        WorkspacePermission
        .EMPLOYEES_VIEW
        .value,

        WorkspacePermission
        .DEPARTMENTS_VIEW
        .value,

        WorkspacePermission
        .TEAMS_VIEW
        .value,

        WorkspacePermission
        .ATTENDANCE_VIEW
        .value,

        WorkspacePermission
        .MEETINGS_VIEW
        .value,

        WorkspacePermission
        .MEETINGS_CREATE
        .value,

        WorkspacePermission
        .GOALS_SELF
        .value,

        WorkspacePermission
        .NOTES_SELF
        .value,

        WorkspacePermission
        .KNOWLEDGE_SELF
        .value,

        WorkspacePermission
        .AI_PRODUCTIVITY_USE
        .value,

        WorkspacePermission
        .TIMELINE_SELF
        .value,

        WorkspacePermission
        .LEAVE_SELF_READ
        .value,

        # -------------------------------------------------
        # Canonical scoped permissions
        # -------------------------------------------------

        WorkspacePermission
        .WORKSPACE_READ
        .value,

        WorkspacePermission
        .EMPLOYEES_SELF_READ
        .value,

        WorkspacePermission
        .DEPARTMENTS_READ
        .value,

        WorkspacePermission
        .TEAMS_READ
        .value,

        WorkspacePermission
        .ATTENDANCE_SELF_READ
        .value,

        # -------------------------------------------------
        # Phase 12.1 — My Schedule / Holidays
        # -------------------------------------------------

        WorkspacePermission
        .SHIFTS_SELF_READ
        .value,

        WorkspacePermission
        .HOLIDAYS_SELF_READ
        .value,

        # -------------------------------------------------
        # Compensation
        # -------------------------------------------------

        WorkspacePermission
        .COMPENSATION_SELF_READ
        .value,

        # -------------------------------------------------
        # Monitoring
        # -------------------------------------------------

        WorkspacePermission
        .MONITORING_SELF_READ
        .value,

        # -------------------------------------------------
        # Devices
        # -------------------------------------------------

        WorkspacePermission
        .DEVICES_SELF_READ
        .value,

        # -------------------------------------------------
        # Tasks / Communication
        # -------------------------------------------------

        WorkspacePermission
        .TASKS_SELF_READ
        .value,

        WorkspacePermission
        .CHANNELS_READ
        .value,

        WorkspacePermission
        .MEETINGS_READ
        .value,

        # -------------------------------------------------
        # Reports
        # -------------------------------------------------

        WorkspacePermission
        .REPORTS_SELF_READ
        .value,

        # -------------------------------------------------
        # Analytics
        # -------------------------------------------------

        WorkspacePermission
        .ANALYTICS_SELF_READ
        .value,

        # -------------------------------------------------
        # Productivity Insights
        # -------------------------------------------------

        WorkspacePermission
        .PRODUCTIVITY_INSIGHTS_SELF_READ
        .value,

        # -------------------------------------------------
        # Integrations
        # -------------------------------------------------

        WorkspacePermission
        .INTEGRATIONS_USE
        .value,

        # -------------------------------------------------
        # Notifications
        # -------------------------------------------------

        WorkspacePermission
        .NOTIFICATIONS_READ
        .value,
    }
)


# =========================================================
# CLIENT / GUEST
# =========================================================

# Client receives no internal scheduling, holiday, employee,
# payroll, monitoring or device permissions by default.


CLIENT_PERMISSIONS = frozenset(
    {
        WorkspacePermission
        .WORKSPACE_READ
        .value,

        WorkspacePermission
        .TASKS_SELF_READ
        .value,

        WorkspacePermission
        .CHANNELS_READ
        .value,

        WorkspacePermission
        .MEETINGS_READ
        .value,

        WorkspacePermission
        .MEETINGS_CREATE
        .value,

        WorkspacePermission
        .REPORTS_SELF_READ
        .value,

        WorkspacePermission
        .INTEGRATIONS_USE
        .value,

        WorkspacePermission
        .NOTIFICATIONS_READ
        .value,
    }
)


# =========================================================
# ROLE MAP
# =========================================================


ROLE_PERMISSIONS = {
    OWNER_ROLE: (
        OWNER_PERMISSIONS
    ),

    ADMIN_ROLE: (
        ADMIN_PERMISSIONS
    ),

    MANAGER_ROLE: (
        MANAGER_PERMISSIONS
    ),

    MEMBER_ROLE: (
        MEMBER_PERMISSIONS
    ),

    CLIENT_ROLE: (
        CLIENT_PERMISSIONS
    ),
}


# =========================================================
# HELPERS
# =========================================================


def role_display_name(
    role_key: str,
) -> str:
    normalized = (
        role_key
        .strip()
        .lower()
    )

    return ROLE_DISPLAY_NAMES.get(
        normalized,
        normalized
        .replace(
            "_",
            " ",
        )
        .title(),
    )


def is_builtin_role(
    role_key: str,
) -> bool:
    return (
        role_key
        .strip()
        .lower()
        in BUILT_IN_ROLE_KEYS
    )


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "OWNER_ROLE",
    "ADMIN_ROLE",
    "MANAGER_ROLE",
    "MEMBER_ROLE",
    "CLIENT_ROLE",

    "BUILT_IN_ROLE_KEYS",
    "ROLE_DISPLAY_NAMES",

    "OWNER_PERMISSIONS",
    "ADMIN_PERMISSIONS",
    "MANAGER_PERMISSIONS",
    "MEMBER_PERMISSIONS",
    "CLIENT_PERMISSIONS",

    "ROLE_PERMISSIONS",

    "role_display_name",
    "is_builtin_role",
    "WORKSPACE_ROLE_OWNER",
    "WORKSPACE_ROLE_ADMIN",
    "WORKSPACE_ROLE_MANAGER",
    "WORKSPACE_ROLE_MEMBER",
    "WORKSPACE_ROLE_CLIENT",
]