import type {
  WorkspaceNavigationView,
} from "@/types/workspace-access";

import {
  hasAnyPermission,
  hasPermission,
} from "@/lib/workspace/access";


export function canViewEmployees(
  permissions: readonly string[],
  view: WorkspaceNavigationView,
): boolean {
  return (
    view === "owner" ||
    hasAnyPermission(
      permissions,
      [
        "employees.all.read",
        "employees.team.read",
        "employees.self.read",
      ],
      view,
    )
  );
}


export function canCreateEmployee(
  permissions: readonly string[],
  view: WorkspaceNavigationView,
): boolean {
  return (
    view === "owner" ||
    hasPermission(
      permissions,
      "employees.create",
      view,
    )
  );
}


export function canUpdateEmployee(
  permissions: readonly string[],
  view: WorkspaceNavigationView,
): boolean {
  return (
    view === "owner" ||
    hasPermission(
      permissions,
      "employees.update",
      view,
    )
  );
}


export function canReadAllEmployees(
  permissions: readonly string[],
  view: WorkspaceNavigationView,
): boolean {
  return (
    view === "owner" ||
    hasPermission(
      permissions,
      "employees.all.read",
      view,
    )
  );
}


export function canReadTeamEmployees(
  permissions: readonly string[],
  view: WorkspaceNavigationView,
): boolean {
  return (
    view === "owner" ||
    hasPermission(
      permissions,
      "employees.team.read",
      view,
    )
  );
}


export function canReadSelfEmployee(
  permissions: readonly string[],
  view: WorkspaceNavigationView,
): boolean {
  return (
    view === "owner" ||
    hasPermission(
      permissions,
      "employees.self.read",
      view,
    )
  );
}