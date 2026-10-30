import type { WorkspaceType } from "@/types/workspace";

export const WORKSPACE_TEMPLATES = {
  company: {
    title: "Company", home: "Workspace Home", organization: "Organization",
    profile: "Company", departments: "Departments", teams: "Teams",
    employees: "Employees", members: "Members", clients: "Clients",
    people: "Human Resources", work: "Work", finance: "Finance",
    monitoring: "Monitoring", ai: "Workspace AI", reports: "Reports",
    projects: "Projects", tasks: "Tasks", updates: "Company updates",
    description: "Manage your company, employees, departments and daily operations.",
  },
  agency: {
    title: "Agency", home: "Agency Home", organization: "Agency",
    profile: "Agency", departments: "Service Departments", teams: "Delivery Teams",
    employees: "Agency Team", members: "Members", clients: "Client Accounts",
    people: "People & HR", work: "Client Work", finance: "Agency Finance",
    monitoring: "Team Monitoring", ai: "Agency AI", reports: "Agency Reports",
    projects: "Client Projects", tasks: "Tasks & Deliverables", updates: "Agency updates",
    description: "Organize your agency, delivery teams, client projects and people.",
  },
} as const;

export function getWorkspaceTemplate(type?: WorkspaceType | null) {
  return WORKSPACE_TEMPLATES[type === "agency" ? "agency" : "company"];
}

export function workspacePageLabel(pathname: string, type?: WorkspaceType | null): string | undefined {
  const words = getWorkspaceTemplate(type);
  const path = pathname.split("?")[0] ?? "";
  if (path === "/workspaces/new") return "Create workspace";
  if (path === "/settings/workspace") return words.profile;
  const segment = path.split("/").filter(Boolean)[0] ?? "";
  return ({ dashboard: words.home, departments: words.departments, teams: words.teams,
    employees: words.employees, members: words.members, clients: words.clients,
    projects: words.projects, tasks: words.tasks, monitoring: words.monitoring,
    reports: words.reports, knowledge: words.ai } as Record<string, string>)[segment];
}


