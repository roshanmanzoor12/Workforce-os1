export interface ChannelReadState {
  channel_id: string;

  user_id: string;

  last_read_message_id:
    | string
    | null;

  last_read_at:
    | string
    | null;

  unread_count: number;
}


export interface ChannelUnreadSummary {
  channel_id: string;

  unread_count: number;

  last_read_message_id:
    | string
    | null;

  last_read_at:
    | string
    | null;
}


export interface WorkspaceChannelUnreadListResponse {
  workspace_id: string;

  total_unread: number;

  channels:
    ChannelUnreadSummary[];
}