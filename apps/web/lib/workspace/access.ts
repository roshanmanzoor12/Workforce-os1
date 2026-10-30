import type {
  WorkspaceNavigationView,
} from "@/types/workspace-access";


const PREVIEW_PERMISSION_SETS:
  Record<
    WorkspaceNavigationView,
    readonly string[]
  > = {
    owner: [
      "*",
    ],

    admin: [
      "workspace.read",

      "workspace.settings.read",
      "workspace.settings.manage",

      "members.read",
      "members.invite",
      "members.update",
      "members.kick",
      "members.ban",
      "members.mute",
      "members.deafen",
      "members.hide",

      "roles.read",
      "roles.assign",
      "roles.manage",

      "employees.all.read",
      "employees.create",
      "employees.update",

      "departments.read",
      "departments.manage",

      "teams.read",
      "teams.manage",

      "attendance.all.read",
      "attendance.manage",
      "attendance.approve",

      "payroll.read",
      "payroll.manage",

      "monitoring.all.read",
      "monitoring.live_screen",

      "devices.all.read",
      "devices.manage",

      "tasks.all.read",
      "tasks.create",
      "tasks.assign.all",
      "tasks.manage",

      "channels.read",
      "channels.create",
      "channels.manage",

      "meetings.read",
      "meetings.create",
      "meetings.invite.all",
      "meetings.manage",

      "reports.all.read",
      "reports.export",

      "integrations.use",
      "integrations.manage",
      "integrations.assign",

      "audit.read",
    ],

    manager: [
      "workspace.read",

      "employees.team.read",

      "departments.read",
      "teams.read",

      "attendance.team.read",
      "attendance.approve",

      "monitoring.team.read",

      "devices.team.read",

      "tasks.team.read",
      "tasks.create",
      "tasks.assign.team",

      "channels.read",

      "meetings.read",
      "meetings.create",
      "meetings.invite.team",

      "reports.team.read",

      "integrations.use",

      "workspace.settings.read",
    ],

    member: [
      "workspace.read",

      "employees.self.read",
      "employees.team.read",

      "departments.read",
      "teams.read",

      "attendance.self.read",

      "compensation.self.read",

      "monitoring.self.read",

      "devices.self.read",

      "tasks.self.read",

      "channels.read",

      "meetings.read",
      "meetings.create",

      "reports.self.read",

      "integrations.use",

      "workspace.settings.read",
    ],

    client: [
      "workspace.read",

      "tasks.self.read",

      "channels.read",

      "meetings.read",

      "reports.self.read",

      "integrations.use",

      "workspace.settings.read",
    ],
  };


export function normalizeNavigationView(
  value:
    string |
    null |
    undefined,
): WorkspaceNavigationView {
  const normalized =
    value
      ?.trim()
      .toLowerCase();


  switch (
    normalized
  ) {
    case "owner":
      return "owner";

    case "admin":
    case "administrator":
      return "admin";

    case "manager":
    case "senior":
    case "team_lead":
    case "team-lead":
      return "manager";

    case "client":
    case "guest":
      return "client";

    case "employee":
    case "member":
      return "member";

    default:
      /*
       * Custom roles do not currently carry
       * a backend navigation_view/base_role.
       *
       * Their real authority still comes from
       * permissions[].
       */
      return "member";
  }
}


export function hasPermission(
  permissions:
    readonly string[] |
    null |
    undefined,

  permission:
    string,

  navigationView:
    WorkspaceNavigationView,
): boolean {
  /*
   * Workspace owner is the root workspace
   * authority in the product.
   *
   * Backend must still enforce authorization.
   */
  if (
    navigationView ===
    "owner"
  ) {
    return true;
  }


  if (
    !permissions ||
    permissions.length ===
      0
  ) {
    return false;
  }


  return (
    permissions.includes(
      "*",
    ) ||
    permissions.includes(
      permission,
    )
  );
}


export function hasAnyPermission(
  permissions:
    readonly string[] |
    null |
    undefined,

  required:
    readonly string[],

  navigationView:
    WorkspaceNavigationView,
): boolean {
  if (
    required.length ===
    0
  ) {
    return true;
  }


  if (
    navigationView ===
    "owner"
  ) {
    return true;
  }


  return required.some(
    (permission) =>
      hasPermission(
        permissions,
        permission,
        navigationView,
      ),
  );
}


export function hasAllPermissions(
  permissions:
    readonly string[] |
    null |
    undefined,

  required:
    readonly string[],

  navigationView:
    WorkspaceNavigationView,
): boolean {
  if (
    required.length ===
    0
  ) {
    return true;
  }


  if (
    navigationView ===
    "owner"
  ) {
    return true;
  }


  return required.every(
    (permission) =>
      hasPermission(
        permissions,
        permission,
        navigationView,
      ),
  );
}


/**
 * Frontend-only Owner preview permissions.
 *
 * This MUST NOT be sent to the backend and MUST NOT
 * be treated as real authorization.
 */
export function getPreviewPermissions(
  view:
    WorkspaceNavigationView,
): string[] {
  return [
    ...PREVIEW_PERMISSION_SETS[
      view
    ],
  ];
}