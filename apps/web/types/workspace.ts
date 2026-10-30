export type WorkspaceStatus =
  | "provisioning"
  | "ready"
  | "failed"
  | "suspended"
  | "archived";

export type WorkspaceRole =
  | "owner"
  | "admin"
  | "manager"
  | "member"
  | "client"
  | (string & {});

export type MembershipStatus =
  | "active"
  | "invited"
  | "suspended"
  | "removed";

export type WorkspaceType = "company" | "agency";

export interface WorkspacePublic {
  workspace_type?: WorkspaceType;
  id: string;

  name: string;

  slug: string;

  created_by_user_id:
    string;

  status:
    WorkspaceStatus;

  is_active:
    boolean;

  timezone:
    string;

  logo_url:
    string | null;
  primary_color: string;
  accent_color: string;

  created_at:
    string;

  updated_at:
    string;
}

export interface WorkspaceMembershipPublic {
  id: string;

  workspace_id:
    string;

  user_id:
    string;

  role_key:
    WorkspaceRole;

  status:
    MembershipStatus;

  invited_by_user_id:
    string | null;

  invited_at:
    string | null;

  joined_at:
    string | null;

  suspended_at:
    string | null;

  removed_at:
    string | null;

  created_at:
    string;

  updated_at:
    string;
}

export interface TenantDatabasePublic {
  status:
    | "pending"
    | "provisioning"
    | "ready"
    | "failed"
    | "suspended"
    | "decommissioned";

  schema_version:
    string | null;

  provisioned_at:
    string | null;

  created_at:
    string;

  updated_at:
    string;
}

export interface UserWorkspacePublic {
  workspace:
    WorkspacePublic;

  membership:
    WorkspaceMembershipPublic;

  tenant:
    TenantDatabasePublic | null;
}

export interface WorkspaceListResponse {
  workspaces:
    UserWorkspacePublic[];

  total:
    number;
}

export interface WorkspaceDetailResponse {
  workspace:
    WorkspacePublic;

  membership:
    WorkspaceMembershipPublic;

  tenant:
    TenantDatabasePublic | null;
}