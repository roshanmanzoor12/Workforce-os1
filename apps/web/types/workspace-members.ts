export interface WorkspaceMemberModerationPublic {
  is_banned:
    boolean;

  is_muted:
    boolean;

  is_deafened:
    boolean;

  is_hidden:
    boolean;
}


export interface WorkspaceMemberPublic {
  membership_id:
    string;

  user_id:
    string;

  email:
    string;

  username:
    string;

  role_key:
    string;

  status:
    string;

  moderation:
    WorkspaceMemberModerationPublic;
}


export interface WorkspaceMembersResponse {
  workspace_id:
    string;

  members:
    WorkspaceMemberPublic[];
}


export interface UpdateWorkspaceMemberRoleRequest {
  role_key:
    string;
}


export interface WorkspaceMemberVisibilityRequest {
  hidden:
    boolean;
}


export type WorkspaceMemberModerationAction =
  | "kick"
  | "ban"
  | "mute"
  | "deafen";


export interface WorkspaceMemberActionResponse {
  message:
    string;

  membership_id:
    string;

  moderation:
    WorkspaceMemberModerationPublic;
}