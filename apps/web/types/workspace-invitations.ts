export type WorkspaceInvitationStatus =
  | "pending"
  | "accepted"
  | "declined"
  | "expired"
  | "revoked";


export interface WorkspaceInvitationPublic {
  workspace_name?: string | null;

  id:
    string;

  workspace_id:
    string;

  employee_id:
    string | null;

  email:
    string;

  invited_user_id:
    string | null;

  role_key:
    string;

  department_id:
    string | null;

  team_id:
    string | null;

  manager_membership_id:
    string | null;

  invited_by_user_id:
    string;

  status:
    WorkspaceInvitationStatus;

  expires_at:
    string;

  accepted_at:
    string | null;

  declined_at:
    string | null;

  revoked_at:
    string | null;

  created_at:
    string;

  updated_at:
    string;
}


export interface CreateWorkspaceInvitationRequest {
  email?:
    string;

  identifier?: string;

  employee_id?:
    string | null;

  role_key?:
    string;

  department_id?:
    string | null;

  team_id?:
    string | null;

  manager_membership_id?:
    string | null;

  expires_at?:
    string | null;
}


export interface WorkspaceInvitationSecretResponse {
  invitation:
    WorkspaceInvitationPublic;

  invitation_token:
    string;
}


/*
 * Compatibility alias for older imports.
 */
export type CreateWorkspaceInvitationResponse =
  WorkspaceInvitationSecretResponse;


export interface WorkspaceInvitationListResponse {
  workspace_id:
    string;

  items?:
    WorkspaceInvitationPublic[];

  total:
    number;
}


/*
 * Compatibility alias for existing frontend code.
 */
export type WorkspaceInvitationsResponse =
  WorkspaceInvitationListResponse;


export interface WorkspaceInvitationTokenPublic {
  invitation_id:
    string | null;

  workspace_id:
    string;

  workspace_name:
    string | null;

  email:
    string;

  role_key:
    string;

  status:
    WorkspaceInvitationStatus;

  expires_at:
    string;
}


export interface WorkspaceInvitationActionResponse {
  message:
    string;

  success?:
    boolean;

  workspace_id:
    string | null;

  membership_id:
    string | null;
}

export interface IncomingWorkspaceInvitationsResponse { items: WorkspaceInvitationPublic[]; total: number; }
