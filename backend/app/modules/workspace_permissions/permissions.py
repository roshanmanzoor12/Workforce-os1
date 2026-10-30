from __future__ import annotations

from enum import StrEnum


class WorkspacePermission(StrEnum):

    # =====================================================
    # WORKSPACE
    # =====================================================

    WORKSPACE_VIEW = (
        "workspace.view"
    )

    WORKSPACE_READ = (
        "workspace.read"
    )

    WORKSPACE_MANAGE = (
        "workspace.manage"
    )

    WORKSPACE_SETTINGS_READ = (
        "workspace.settings.read"
    )

    WORKSPACE_SETTINGS_MANAGE = (
        "workspace.settings.manage"
    )

    # =====================================================
    # MEMBERS
    # =====================================================

    MEMBERS_VIEW = (
        "members.view"
    )

    MEMBERS_READ = (
        "members.read"
    )

    MEMBERS_MANAGE = (
        "members.manage"
    )

    MEMBERS_INVITE = (
        "members.invite"
    )

    MEMBERS_UPDATE = (
        "members.update"
    )

    MEMBERS_REMOVE = (
        "members.remove"
    )

    MEMBERS_KICK = (
        "members.kick"
    )

    MEMBERS_BAN = (
        "members.ban"
    )

    MEMBERS_MUTE = (
        "members.mute"
    )

    MEMBERS_DEAFEN = (
        "members.deafen"
    )

    MEMBERS_HIDE = (
        "members.hide"
    )

    # =====================================================
    # ROLES
    # =====================================================

    ROLES_READ = (
        "roles.read"
    )

    ROLES_ASSIGN = (
        "roles.assign"
    )

    ROLES_MANAGE = (
        "roles.manage"
    )

    # =====================================================
    # EMPLOYEES
    # =====================================================

    EMPLOYEES_VIEW = (
        "employees.view"
    )

    EMPLOYEES_MANAGE = (
        "employees.manage"
    )

    EMPLOYEES_READ = (
        "employees.read"
    )

    EMPLOYEES_SELF_READ = (
        "employees.self.read"
    )

    EMPLOYEES_TEAM_READ = (
        "employees.team.read"
    )

    EMPLOYEES_ALL_READ = (
        "employees.all.read"
    )

    EMPLOYEES_CREATE = (
        "employees.create"
    )

    EMPLOYEES_UPDATE = (
        "employees.update"
    )

    EMPLOYEES_DELETE = (
        "employees.delete"
    )

    # =====================================================
    # ORGANIZATION
    # =====================================================

    DEPARTMENTS_VIEW = (
        "departments.view"
    )

    DEPARTMENTS_READ = (
        "departments.read"
    )

    DEPARTMENTS_MANAGE = (
        "departments.manage"
    )

    TEAMS_VIEW = (
        "teams.view"
    )

    TEAMS_READ = (
        "teams.read"
    )

    TEAMS_MANAGE = (
        "teams.manage"
    )

    # =====================================================
    # ATTENDANCE
    # =====================================================

    ATTENDANCE_VIEW = (
        "attendance.view"
    )

    ATTENDANCE_MANAGE = (
        "attendance.manage"
    )

    ATTENDANCE_SELF_READ = (
        "attendance.self.read"
    )

    ATTENDANCE_TEAM_READ = (
        "attendance.team.read"
    )

    ATTENDANCE_ALL_READ = (
        "attendance.all.read"
    )

    ATTENDANCE_APPROVE = (
        "attendance.approve"
    )

    # =====================================================
    # SHIFTS / SCHEDULING
    # =====================================================

    SHIFTS_VIEW = (
        "shifts.view"
    )

    SHIFTS_MANAGE = (
        "shifts.manage"
    )

    SHIFTS_SELF_READ = (
        "shifts.self.read"
    )

    SHIFTS_TEAM_READ = (
        "shifts.team.read"
    )

    SHIFTS_ALL_READ = (
        "shifts.all.read"
    )

    # =====================================================
    # HOLIDAYS
    # =====================================================

    HOLIDAYS_VIEW = (
        "holidays.view"
    )

    HOLIDAYS_MANAGE = (
        "holidays.manage"
    )

    HOLIDAYS_SELF_READ = (
        "holidays.self.read"
    )

    HOLIDAYS_TEAM_READ = (
        "holidays.team.read"
    )

    HOLIDAYS_ALL_READ = (
        "holidays.all.read"
    )


    # =====================================================
    # LEAVE
    # =====================================================

    LEAVE_VIEW = "leave.view"
    LEAVE_MANAGE = "leave.manage"

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

    # =====================================================
    # COMPENSATION / PAYROLL
    # =====================================================

    COMPENSATION_SELF_READ = (
        "compensation.self.read"
    )

    PAYROLL_READ = (
        "payroll.read"
    )

    PAYROLL_MANAGE = (
        "payroll.manage"
    )

    # =====================================================
    # MONITORING
    # =====================================================

    MONITORING_VIEW = (
        "monitoring.view"
    )

    MONITORING_MANAGE = (
        "monitoring.manage"
    )

    MONITORING_SELF_READ = (
        "monitoring.self.read"
    )

    MONITORING_TEAM_READ = (
        "monitoring.team.read"
    )

    MONITORING_ALL_READ = (
        "monitoring.all.read"
    )

    MONITORING_LIVE_VIEW = (
        "monitoring.live_view"
    )

    MONITORING_LIVE_SCREEN = (
        "monitoring.live_screen"
    )

    MONITORING_SETTINGS_MANAGE = (
        "monitoring.settings.manage"
    )

    # =====================================================
    # DEVICES
    # =====================================================

    DEVICES_SELF_READ = (
        "devices.self.read"
    )

    DEVICES_TEAM_READ = (
        "devices.team.read"
    )

    DEVICES_ALL_READ = (
        "devices.all.read"
    )

    DEVICES_MANAGE = (
        "devices.manage"
    )

    # =====================================================
    # TASKS
    # =====================================================

    TASKS_SELF_READ = (
        "tasks.self.read"
    )

    TASKS_TEAM_READ = (
        "tasks.team.read"
    )

    TASKS_ALL_READ = (
        "tasks.all.read"
    )

    TASKS_CREATE = (
        "tasks.create"
    )

    TASKS_ASSIGN_TEAM = (
        "tasks.assign.team"
    )

    TASKS_ASSIGN_ALL = (
        "tasks.assign.all"
    )

    TASKS_MANAGE = (
        "tasks.manage"
    )

    # =====================================================
    # MEETINGS
    # =====================================================

    MEETINGS_VIEW = (
        "meetings.view"
    )

    MEETINGS_READ = (
        "meetings.read"
    )

    MEETINGS_CREATE = (
        "meetings.create"
    )

    MEETINGS_MANAGE = (
        "meetings.manage"
    )

    MEETINGS_INVITE_TEAM = (
        "meetings.invite.team"
    )

    MEETINGS_INVITE_ALL = (
        "meetings.invite.all"
    )

    MEETINGS_INVITE_EXTERNAL = (
        "meetings.invite.external"
    )

    # =====================================================
    # CHANNELS
    # =====================================================

    CHANNELS_READ = (
        "channels.read"
    )

    CHANNELS_CREATE = (
        "channels.create"
    )

    CHANNELS_MANAGE = (
        "channels.manage"
    )

    # =====================================================
    # GOALS
    # =====================================================

    GOALS_VIEW = (
        "goals.view"
    )

    GOALS_MANAGE = (
        "goals.manage"
    )

    GOALS_SELF = (
        "goals.self"
    )

    # =====================================================
    # NOTES
    # =====================================================

    NOTES_VIEW = (
        "notes.view"
    )

    NOTES_MANAGE = (
        "notes.manage"
    )

    NOTES_SELF = (
        "notes.self"
    )

    # =====================================================
    # KNOWLEDGE
    # =====================================================

    KNOWLEDGE_VIEW = (
        "knowledge.view"
    )

    KNOWLEDGE_MANAGE = (
        "knowledge.manage"
    )

    KNOWLEDGE_SELF = (
        "knowledge.self"
    )

    # =====================================================
    # TIMELINE
    # =====================================================

    TIMELINE_VIEW = (
        "timeline.view"
    )

    TIMELINE_SELF = (
        "timeline.self"
    )

    # =====================================================
    # REPORTS
    # =====================================================

    REPORTS_VIEW = (
        "reports.view"
    )

    REPORTS_SELF_READ = (
        "reports.self.read"
    )

    REPORTS_TEAM_READ = (
        "reports.team.read"
    )

    REPORTS_ALL_READ = (
        "reports.all.read"
    )

    REPORTS_EXPORT = (
        "reports.export"
    )

    # =====================================================
    # ANALYTICS
    # =====================================================

    ANALYTICS_SELF_READ = (
        "analytics.self.read"
    )

    ANALYTICS_TEAM_READ = (
        "analytics.team.read"
    )

    ANALYTICS_ALL_READ = (
        "analytics.all.read"
    )

    ANALYTICS_EXPORT = (
        "analytics.export"
    )

    # =====================================================
    # PRODUCTIVITY INSIGHTS
    # =====================================================

    PRODUCTIVITY_INSIGHTS_SELF_READ = (
        "productivity_insights.self.read"
    )

    PRODUCTIVITY_INSIGHTS_TEAM_READ = (
        "productivity_insights.team.read"
    )

    PRODUCTIVITY_INSIGHTS_ALL_READ = (
        "productivity_insights.all.read"
    )

    PRODUCTIVITY_INSIGHTS_EXPORT = (
        "productivity_insights.export"
    )

    # =====================================================
    # INTEGRATIONS
    # =====================================================

    INTEGRATIONS_USE = (
        "integrations.use"
    )

    INTEGRATIONS_MANAGE = (
        "integrations.manage"
    )

    INTEGRATIONS_ASSIGN = (
        "integrations.assign"
    )

    # =====================================================
    # BILLING
    # =====================================================

    BILLING_READ = (
        "billing.read"
    )

    BILLING_MANAGE = (
        "billing.manage"
    )

    # =====================================================
    # AI
    # =====================================================

    AI_PRODUCTIVITY_USE = (
        "ai_productivity.use"
    )

    AI_PRODUCTIVITY_MANAGE = (
        "ai_productivity.manage"
    )

    # =====================================================
    # NOTIFICATIONS / AUDIT
    # =====================================================

    NOTIFICATIONS_READ = (
        "notifications.read"
    )

    AUDIT_VIEW = (
        "audit.view"
    )

    AUDIT_READ = (
        "audit.read"
    )

    # Projects
    PROJECTS_VIEW = "projects.view"
    PROJECTS_MANAGE = "projects.manage"


ALL_WORKSPACE_PERMISSIONS = frozenset(
    permission.value
    for permission
    in WorkspacePermission
)


__all__ = [
    "WorkspacePermission",
    "ALL_WORKSPACE_PERMISSIONS",
]