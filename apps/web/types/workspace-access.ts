import type {
  WorkspaceRolePublic,
} from "@/types/workspace-roles";

export type WorkspaceNavigationView =
  | "owner"
  | "admin"
  | "manager"
  | "member"
  | "client";

export interface WorkspaceMemberModerationPublic {
  is_muted:
    boolean;

  is_deafened:
    boolean;

  is_hidden:
    boolean;

  is_banned?:
    boolean;
}

export interface WorkspaceBootstrapResponse {
  billing?: {
    plan_code: string;
    features: {
      monitoring: boolean;
      live_screen: boolean;
      advanced_analytics: boolean;
    };
  };

  workspace_id:
    string;

  membership_id:
    string;

  role_key:
    string;

  permissions:
    string[];

  moderation:
    WorkspaceMemberModerationPublic;

  available_roles:
    WorkspaceRolePublic[];
}

export type WorkspaceScopeType =
  | "self"
  | "team"
  | "department"
  | "workspace"
  | "shared";

export interface WorkspaceScopePublic {
  type:
    WorkspaceScopeType;

  id:
    string | null;
}

export interface WorkspaceEmployeeAccessPublic {
  id:
    string;

  employee_code:
    string | null;

  department_id:
    string | null;

  team_id:
    string | null;

  manager_membership_id:
    string | null;

  status:
    string;
}

export interface WorkspaceFeatureEntitlements {
  plan_code:
    string;

  monitoring:
    boolean;

  live_screen:
    boolean;

  advanced_analytics:
    boolean;
}
