export type WorkspaceChannelType =
  | "text"
  | "announcement";


export type WorkspaceChannelMessageType =
  | "text"
  | "system";


export interface WorkspaceChannelPublic {
  id:
    string;

  workspace_id:
    string;

  name:
    string;

  slug:
    string;

  channel_type:
    WorkspaceChannelType;

  created_by_user_id:
    string;

  is_active:
    boolean;

  created_at:
    string;

  updated_at:
    string;
}


export interface WorkspaceChannelCreateRequest {
  workspace_id:
    string;

  name:
    string;

  channel_type?:
    WorkspaceChannelType;
}


export interface WorkspaceChannelUpdateRequest {
  name:
    string;
}


export interface WorkspaceChannelMessagePublic {
  id:
    string;

  channel_id:
    string;

  sender_user_id:
    string | null;

  message_type:
    WorkspaceChannelMessageType;

  content:
    string;

  edited_at:
    string | null;

  deleted_at:
    string | null;

  created_at:
    string;
}


export interface WorkspaceChannelMessageCreateRequest {
  content:
    string;
}