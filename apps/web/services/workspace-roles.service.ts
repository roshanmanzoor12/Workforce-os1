import {
  api,
} from "@/lib/api/client";

import type {
  CreateWorkspaceRoleRequest,
  UpdateWorkspaceRoleRequest,
  WorkspaceRolePublic,
  WorkspaceRolesResponse,
} from "@/types/workspace-roles";

import type {
  RawWorkspacePermissionsResponse,
  WorkspacePermissionDefinition,
  WorkspacePermissionsResponse,
} from "@/types/workspace-permissions";


const GROUP_NAMES:
  Record<string, string> = {
    workspace:
      "Workspace",

    members:
      "Members & Invitations",

    roles:
      "Roles & Access",

    employees:
      "Employees",

    departments:
      "Departments",

    teams:
      "Teams",

    attendance:
      "Attendance",

    compensation:
      "Compensation",

    payroll:
      "Payroll",

    monitoring:
      "Monitoring & Activity",

    devices:
      "Devices",

    tasks:
      "Tasks",

    channels:
      "Channels & Chat",

    meetings:
      "Meetings & Calls",

    goals:
      "Goals",

    notes:
      "Notes",

    knowledge:
      "Knowledge",

    timeline:
      "Timeline",

    reports:
      "Reports",

    analytics:
      "Analytics",

    productivity_insights:
      "Productivity Insights",

    integrations:
      "Integrations",

    billing:
      "Billing",

    ai_productivity:
      "AI Productivity",

    notifications:
      "Notifications",

    audit:
      "Audit & Security",
  };


const ACTION_NAMES:
  Record<string, string> = {
    view:
      "View",

    read:
      "Read",

    create:
      "Create",

    update:
      "Update",

    manage:
      "Manage",

    delete:
      "Delete",

    remove:
      "Remove",

    invite:
      "Invite",

    assign:
      "Assign",

    approve:
      "Approve",

    export:
      "Export",

    use:
      "Use",

    kick:
      "Kick",

    ban:
      "Ban",

    mute:
      "Mute",

    deafen:
      "Deafen",

    hide:
      "Hide",

    live_view:
      "View Live Monitoring",

    live_screen:
      "View Live Screen",
  };


const SCOPE_NAMES:
  Record<string, string> = {
    all:
      "All",

    team:
      "Team",

    self:
      "Own",

    workspace:
      "Workspace",

    department:
      "Department",

    shared:
      "Shared",

    external:
      "External",
  };


function humanize(
  value:
    string,
): string {
  return value
    .replace(
      /[_-]+/g,
      " ",
    )
    .split(" ")
    .filter(
      Boolean,
    )
    .map(
      (
        part,
      ) =>
        part
          .charAt(
            0,
          )
          .toUpperCase() +
        part.slice(
          1,
        ),
    )
    .join(" ");
}


function permissionGroup(
  key:
    string,
): string {
  const [
    resource =
      "other",
  ] =
    key
      .split(".")
      .filter(
        Boolean,
      );


  return (
    GROUP_NAMES[
      resource
    ] ??
    humanize(
      resource,
    )
  );
}


function permissionDisplayName(
  key:
    string,
): string {
  const parts =
    key
      .split(".")
      .filter(
        Boolean,
      );


  const [
    resource =
      "permission",

    ...remaining
  ] =
    parts;


  if (
    remaining.length ===
    0
  ) {
    return humanize(
      resource,
    );
  }


  const firstRemaining =
    remaining[0];


  if (
    remaining.length >=
      2 &&
    firstRemaining &&
    SCOPE_NAMES[
      firstRemaining
    ]
  ) {
    const scope =
      SCOPE_NAMES[
        firstRemaining
      ] ??
      humanize(
        firstRemaining,
      );


    const actionKey =
      remaining
        .slice(
          1,
        )
        .join("_");


    const action =
      ACTION_NAMES[
        actionKey
      ] ??
      humanize(
        actionKey,
      );


    return `${action} ${scope} ${humanize(
      resource,
    )}`;
  }


  if (
    remaining.length >=
    2
  ) {
    const last =
      remaining[
        remaining.length -
        1
      ];

    const first =
      remaining[0];


    if (
      last &&
      first &&
      SCOPE_NAMES[
        last
      ]
    ) {
      const scope =
        SCOPE_NAMES[
          last
        ] ??
        humanize(
          last,
        );


      const actionKey =
        remaining
          .slice(
            0,
            -1,
          )
          .join("_");


      const action =
        ACTION_NAMES[
          actionKey
        ] ??
        humanize(
          actionKey,
        );


      return `${action} ${scope} ${humanize(
        resource,
      )}`;
    }
  }


  const actionKey =
    remaining.join(
      "_",
    );


  const action =
    ACTION_NAMES[
      actionKey
    ] ??
    humanize(
      actionKey,
    );


  return `${action} ${humanize(
    resource,
  )}`;
}


function permissionDescription(
  key:
    string,
): string {
  return `${permissionDisplayName(
    key,
  )} permission inside this workspace.`;
}


function permissionDangerous(
  key:
    string,
): boolean {
  const dangerousSegments =
    [
      ".delete",
      ".remove",
      ".ban",
      ".kick",
      "billing.manage",
      "payroll.manage",
      "roles.manage",
      "members.update",
      "members.manage",
      "workspace.manage",
      "workspace.settings.manage",
      "monitoring.manage",
      "monitoring.settings.manage",
    ];


  return dangerousSegments.some(
    (
      segment,
    ) =>
      key.includes(
        segment,
      ),
  );
}


function normalizePermission(
  input:
    unknown,
):
  WorkspacePermissionDefinition |
  null {
  if (
    typeof input ===
    "string"
  ) {
    const key =
      input.trim();


    if (
      !key
    ) {
      return null;
    }


    return {
      key,

      display_name:
        permissionDisplayName(
          key,
        ),

      description:
        permissionDescription(
          key,
        ),

      group:
        permissionGroup(
          key,
        ),

      dangerous:
        permissionDangerous(
          key,
        ),
    };
  }


  if (
    typeof input ===
      "object" &&
    input !==
      null
  ) {
    const raw =
      input as Record<
        string,
        unknown
      >;


    let key:
      string |
      null =
      null;


    if (
      typeof raw.key ===
      "string"
    ) {
      key =
        raw.key;
    } else if (
      typeof raw.permission ===
      "string"
    ) {
      key =
        raw.permission;
    } else if (
      typeof raw.code ===
      "string"
    ) {
      key =
        raw.code;
    }


    if (
      !key
    ) {
      return null;
    }


    const displayName =
      typeof raw.display_name ===
        "string"
        ? raw.display_name
        : typeof raw.name ===
            "string"
          ? raw.name
          : permissionDisplayName(
              key,
            );


    const description =
      typeof raw.description ===
        "string"
        ? raw.description
        : permissionDescription(
            key,
          );


    let group =
      permissionGroup(
        key,
      );


    if (
      typeof raw.group ===
      "string"
    ) {
      group =
        raw.group;
    }


    if (
      typeof raw.group ===
        "object" &&
      raw.group !==
        null
    ) {
      const rawGroup =
        raw.group as Record<
          string,
          unknown
        >;


      if (
        typeof rawGroup.name ===
        "string"
      ) {
        group =
          rawGroup.name;
      }
    }


    return {
      key,

      display_name:
        displayName,

      description,

      group,

      dangerous:
        typeof raw.dangerous ===
          "boolean"
          ? raw.dangerous
          : permissionDangerous(
              key,
            ),
    };
  }


  return null;
}


function normalizeRole(
  role:
    WorkspaceRolePublic,
):
  WorkspaceRolePublic {
  return {
    ...role,

    permissions:
      Array.isArray(
        role.permissions,
      )
        ? role.permissions
        : [],

    is_active:
      role.is_active ??
      true,

    is_builtin:
      role.is_builtin ??
      false,

    is_immutable:
      role.is_immutable ??
      false,
  };
}


async function list(
  workspaceId:
    string,
): Promise<WorkspaceRolesResponse> {
  const response =
    await api.get<WorkspaceRolesResponse>(
      `/workspaces/${workspaceId}/roles`,
    );


  return {
    ...response,

    roles:
      Array.isArray(
        response.roles,
      )
        ? response.roles.map(
            normalizeRole,
          )
        : [],
  };
}


async function listPermissions(
  workspaceId:
    string,
): Promise<WorkspacePermissionsResponse> {
  const response =
    await api.get<RawWorkspacePermissionsResponse>(
      `/workspaces/${workspaceId}/permissions`,
    );


  const rawPermissions =
    Array.isArray(
      response.permissions,
    )
      ? response.permissions
      : [];


  const normalized:
    WorkspacePermissionDefinition[] =
    [];


  for (
    const rawPermission
    of rawPermissions
  ) {
    const permission =
      normalizePermission(
        rawPermission,
      );


    if (
      permission
    ) {
      normalized.push(
        permission,
      );
    }
  }


  const seen =
    new Set<string>();


  const permissions:
    WorkspacePermissionDefinition[] =
    [];


  for (
    const permission
    of normalized
  ) {
    if (
      seen.has(
        permission.key,
      )
    ) {
      continue;
    }


    seen.add(
      permission.key,
    );


    permissions.push(
      permission,
    );
  }


  return {
    permissions,
  };
}


async function create(
  workspaceId:
    string,

  payload:
    CreateWorkspaceRoleRequest,
): Promise<WorkspaceRolePublic> {
  const response =
    await api.post<WorkspaceRolePublic>(
      `/workspaces/${workspaceId}/roles`,
      payload,
    );


  return normalizeRole(
    response,
  );
}


async function update(
  workspaceId:
    string,

  roleId:
    string,

  payload:
    UpdateWorkspaceRoleRequest,
): Promise<WorkspaceRolePublic> {
  const response =
    await api.patch<WorkspaceRolePublic>(
      `/workspaces/${workspaceId}/roles/${roleId}`,
      payload,
    );


  return normalizeRole(
    response,
  );
}


async function updateBuiltin(
  workspaceId: string,
  roleKey: string,
  payload: { permissions: string[] },
): Promise<WorkspaceRolePublic> {
  const response = await api.put<WorkspaceRolePublic>(
    `/workspaces/${workspaceId}/roles/builtin/${encodeURIComponent(roleKey)}`,
    payload,
  );
  return normalizeRole(response);
}


async function remove(
  workspaceId:
    string,

  roleId:
    string,
): Promise<void> {
  await api.delete<void>(
    `/workspaces/${workspaceId}/roles/${roleId}`,
  );
}


export const workspaceRolesService = {
  updateBuiltin,

  list,

  listPermissions,

  create,

  update,

  remove,
};