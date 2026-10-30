
import type { LucideIcon } from "lucide-react";

import {
  BarChart3,
  Building2,
  CalendarDays,
  Clock3,
  CreditCard,
  FileText,
  Folder,
  Home,
  Laptop2,
  Link2,
  MessageSquareMore,
  MonitorUp,
  Puzzle,
  Settings,
  ShieldCheck,
  Sparkles,
  Target,
  Users,
  UsersRound,
  Video,
} from "lucide-react";

import type {
  WorkspaceNavigationView,
} from "@/types/workspace-access";

import type {
  WorkspaceType,
} from "@/types/workspace";

import {
  getWorkspaceTemplate,
} from "./templates";

export type WorkspaceEntitlementKey =
  | "monitoring"
  | "live_screen"
  | "advanced_analytics";

export type WorkspaceNavigationGroup =
  | "organization"
  | "people"
  | "communication"
  | "work"
  | "finance"
  | "monitoring"
  | "administration";

export interface WorkspaceNavigationItem {
  key: string;
  label: string;
  href: string;
  icon: LucideIcon;
  group?: WorkspaceNavigationGroup;
  anyPermissions?: string[];
  entitlement?: WorkspaceEntitlementKey;
}

const MODULES: WorkspaceNavigationItem[] = [
  {
    key: "dashboard",
    label: "Home",
    href: "/dashboard",
    icon: Home,
  },
  {
    key: "workspace-ai",
    label: "Workspace AI",
    href: "/knowledge",
    icon: Sparkles,
    anyPermissions: ["workspace.read"],
  },

  // ORGANIZATION

  {
    key: "company",
    label: "Company",
    href: "/settings/workspace",
    icon: Building2,
    group: "organization",
    anyPermissions: [
      "workspace.settings.read",
      "workspace.settings.manage",
    ],
  },
  {
    key: "departments",
    label: "Departments",
    href: "/departments",
    icon: Building2,
    group: "organization",
    anyPermissions: [
      "departments.read",
      "departments.manage",
      "teams.read",
      "teams.manage",
    ],
  },
  {
    key: "teams",
    label: "Teams",
    href: "/teams",
    icon: UsersRound,
    group: "organization",
    anyPermissions: [
      "teams.read",
      "teams.manage",
    ],
  },
  {
    key: "employees",
    label: "Employees",
    href: "/employees",
    icon: Users,
    group: "organization",
    anyPermissions: [
      "employees.all.read",
      "employees.team.read",
      "employees.self.read",
      "employees.create",
      "employees.update",
    ],
  },
  {
    key: "members",
    label: "Members",
    href: "/members",
    icon: Users,
    group: "organization",
    anyPermissions: ["members.read"],
  },
  {
    key: "clients",
    label: "Clients",
    href: "/clients",
    icon: Building2,
    group: "organization",
    anyPermissions: ["members.read"],
  },

  // This is the separate device assignment page.
  {
    key: "device-assignments",
    label: "Device Assignments",
    href: "/devices",
    icon: Link2,
    group: "organization",
    anyPermissions: ["devices.manage"],
  },

  // HUMAN RESOURCES

  {
    key: "attendance",
    label: "Attendance",
    href: "/attendance",
    icon: Clock3,
    group: "people",
    anyPermissions: [
      "attendance.all.read",
      "attendance.team.read",
      "attendance.self.read",
      "attendance.manage",
      "attendance.approve",
    ],
  },
  {
    key: "leave",
    label: "Leave",
    href: "/leave",
    icon: CalendarDays,
    group: "people",
    anyPermissions: [
      "attendance.all.read",
      "attendance.team.read",
      "attendance.self.read",
      "attendance.approve",
    ],
  },
  {
    key: "shifts",
    label: "Shifts",
    href: "/shifts",
    icon: Clock3,
    group: "people",
    anyPermissions: [
      "attendance.all.read",
      "attendance.manage",
    ],
  },
  {
    key: "holidays",
    label: "Holidays",
    href: "/holidays",
    icon: CalendarDays,
    group: "people",
    anyPermissions: [
      "attendance.all.read",
      "attendance.team.read",
      "attendance.self.read",
    ],
  },
  {
    key: "recruitment",
    label: "Recruitment",
    href: "/recruitment",
    icon: Users,
    group: "people",
    anyPermissions: [
      "employees.create",
      "employees.update",
    ],
  },
  {
    key: "resume-analyzer",
    label: "Resume Analyzer",
    href: "/resume-analyzer",
    icon: FileText,
    group: "people",
    anyPermissions: ["employees.create"],
  },
  {
    key: "performance",
    label: "Performance",
    href: "/performance",
    icon: BarChart3,
    group: "people",
    anyPermissions: [
      "employees.all.read",
      "employees.team.read",
    ],
  },
  {
    key: "discipline",
    label: "Discipline",
    href: "/discipline",
    icon: ShieldCheck,
    group: "people",
    anyPermissions: ["employees.update"],
  },

  // COMMUNICATION

  {
    key: "channels",
    label: "Channels",
    href: "/channels",
    icon: MessageSquareMore,
    group: "communication",
    anyPermissions: [
      "channels.read",
      "channels.create",
      "channels.manage",
    ],
  },
  {
    key: "meetings",
    label: "Meetings",
    href: "/meetings",
    icon: Video,
    group: "communication",
    anyPermissions: [
      "meetings.read",
      "meetings.create",
      "meetings.invite.all",
      "meetings.invite.team",
      "meetings.manage",
    ],
  },

  // WORK

  {
    key: "projects",
    label: "Projects",
    href: "/projects",
    icon: Folder,
    group: "work",
    anyPermissions: [
      "tasks.all.read",
      "tasks.team.read",
      "tasks.self.read",
      "tasks.create",
    ],
  },
  {
    key: "tasks",
    label: "Tasks",
    href: "/tasks",
    icon: Target,
    group: "work",
    anyPermissions: [
      "tasks.all.read",
      "tasks.team.read",
      "tasks.self.read",
      "tasks.create",
      "tasks.assign.all",
      "tasks.assign.team",
      "tasks.manage",
    ],
  },
  {
    key: "productivity",
    label: "Productivity",
    href: "/productivity",
    icon: BarChart3,
    group: "work",
    anyPermissions: [
      "reports.all.read",
      "reports.team.read",
      "reports.self.read",
    ],
  },

  // FINANCE

  {
    key: "payroll",
    label: "Payroll",
    href: "/payroll",
    icon: CreditCard,
    group: "finance",
    anyPermissions: [
      "payroll.read",
      "payroll.manage",
      "compensation.self.read",
    ],
  },
  {
    key: "billing",
    label: "Plans & Billing",
    href: "/billing/workspace",
    icon: CreditCard,
    group: "finance",
    anyPermissions: ["workspace.settings.manage"],
  },

  // MONITORING

  {
    key: "monitoring",
    label: "Overview",
    href: "/monitoring",
    icon: MonitorUp,
    group: "monitoring",
    anyPermissions: [
      "monitoring.all.read",
      "monitoring.team.read",
      "monitoring.self.read",
      "monitoring.live_screen",
    ],
    entitlement: "monitoring",
  },
  {
    key: "monitoring-employees",
    label: "Employees",
    href: "/monitoring/employees",
    icon: Users,
    group: "monitoring",
    anyPermissions: [
      "monitoring.all.read",
      "monitoring.team.read",
      "monitoring.self.read",
    ],
    entitlement: "monitoring",
  },

  // Monitoring health is NOT device assignment.
  {
    key: "monitoring-devices",
    label: "Devices",
    href: "/monitoring/devices",
    icon: Laptop2,
    group: "monitoring",
    anyPermissions: [
      "monitoring.all.read",
      "monitoring.team.read",
      "devices.all.read",
      "devices.team.read",
      "devices.manage",
    ],
    entitlement: "monitoring",
  },
  {
    key: "live-screens",
    label: "Live Screen",
    href: "/live-screens",
    icon: MonitorUp,
    group: "monitoring",
    anyPermissions: ["monitoring.live_screen"],
    entitlement: "live_screen",
  },
  {
    key: "live-screen-wall",
    label: "Live Screen Wall",
    href: "/monitoring/live-wall",
    icon: MonitorUp,
    group: "monitoring",
    anyPermissions: ["monitoring.live_screen"],
    entitlement: "live_screen",
  },
  {
    key: "screenshots",
    label: "Screenshots",
    href: "/monitoring/screenshots",
    icon: FileText,
    group: "monitoring",
    anyPermissions: [
      "monitoring.all.read",
      "monitoring.team.read",
    ],
    entitlement: "monitoring",
  },
  {
    key: "activity",
    label: "Activity",
    href: "/monitoring/activity",
    icon: BarChart3,
    group: "monitoring",
    anyPermissions: [
      "monitoring.all.read",
      "monitoring.team.read",
      "monitoring.self.read",
    ],
    entitlement: "monitoring",
  },
  {
    key: "applications",
    label: "Applications",
    href: "/monitoring/applications",
    icon: Laptop2,
    group: "monitoring",
    anyPermissions: [
      "monitoring.all.read",
      "monitoring.team.read",
    ],
    entitlement: "monitoring",
  },
  {
    key: "websites",
    label: "Websites",
    href: "/monitoring/websites",
    icon: Laptop2,
    group: "monitoring",
    anyPermissions: [
      "monitoring.all.read",
      "monitoring.team.read",
    ],
    entitlement: "monitoring",
  },
  {
    key: "monitoring-attendance",
    label: "Attendance",
    href: "/monitoring/attendance",
    icon: Clock3,
    group: "monitoring",
    anyPermissions: [
      "monitoring.all.read",
      "monitoring.team.read",
      "monitoring.self.read",
    ],
    entitlement: "monitoring",
  },
  {
    key: "monitoring-alerts",
    label: "Alerts",
    href: "/monitoring/alerts",
    icon: ShieldCheck,
    group: "monitoring",
    anyPermissions: [
      "monitoring.all.read",
      "monitoring.team.read",
    ],
    entitlement: "monitoring",
  },
  {
    key: "reports",
    label: "Reports",
    href: "/reports",
    icon: BarChart3,
    group: "monitoring",
    anyPermissions: [
      "reports.all.read",
      "reports.team.read",
      "reports.self.read",
      "reports.export",
    ],
    entitlement: "monitoring",
  },

  // ADMINISTRATION

  {
    key: "roles",
    label: "Roles & Access",
    href: "/roles",
    icon: ShieldCheck,
    group: "administration",
    anyPermissions: [
      "roles.read",
      "roles.assign",
      "roles.manage",
    ],
  },
  {
    key: "invitations",
    label: "Invitations",
    href: "/invitations",
    icon: Users,
    group: "administration",
    anyPermissions: ["members.invite"],
  },
  {
    key: "integrations",
    label: "Integrations",
    href: "/integrations",
    icon: Puzzle,
    group: "administration",
    anyPermissions: [
      "integrations.use",
      "integrations.manage",
      "integrations.assign",
    ],
  },
  {
    key: "audit",
    label: "Audit Log",
    href: "/audit",
    icon: FileText,
    group: "administration",
    anyPermissions: ["audit.read"],
  },
  {
    key: "settings",
    label: "Settings",
    href: "/settings",
    icon: Settings,
    group: "administration",
    anyPermissions: [
      "workspace.read",
      "workspace.settings.read",
      "workspace.settings.manage",
    ],
  },
];

export function getWorkspaceNavigation(
  view: WorkspaceNavigationView,
  type: WorkspaceType = "company"
): WorkspaceNavigationItem[] {
  const words = getWorkspaceTemplate(type);

  const labels: Record<string, string> = {
    company: words.profile,
    departments: words.departments,
    teams: words.teams,
    employees: words.employees,
    clients: words.clients,
    projects: words.projects,
    tasks: words.tasks,
    "workspace-ai": words.ai,
    reports: words.reports,
  };

  return MODULES.map((item) => {
    let label = labels[item.key] ?? item.label;

    if (view === "manager") {
      label =
        (
          {
            employees: "Team Members",
            attendance: "Team Attendance",
            reports: "Team Reports",
          } as Record<string, string>
        )[item.key] ?? label;
    }

    if (view === "member") {
      label =
        (
          {
            attendance: "My Attendance",
            payroll: "My Compensation",
            monitoring: "My Activity",
            tasks: "My Tasks",
          } as Record<string, string>
        )[item.key] ?? label;
    }

    if (view === "client" && item.key === "reports") {
      label = "Shared Reports";
    }

    return {
      ...item,
      label,
    };
  });
}
