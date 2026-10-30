export type ChannelRealtimeEventType =
  | "channel.connected"
  | "channel.disconnected"
  | "channel.message.created"
  | "channel.message.updated"
  | "channel.message.deleted"
  | "channel.attachment.bound"
  | "channel.typing.started"
  | "channel.typing.stopped"
  | "channel.presence.updated"
  | "channel.created"
  | "channel.updated"
  | "channel.archived"
  | "channel.heartbeat";


export type ChannelPresenceState =
  | "online"
  | "idle"
  | "offline";


export interface ChannelRealtimeEvent<
  TPayload = Record<string, unknown>,
> {
  event_id: string;
  event_type: ChannelRealtimeEventType;
  workspace_id: string;
  channel_id: string;
  actor_user_id: string | null;
  sequence: number;
  occurred_at: string;
  payload: TPayload;
}


export interface ChannelRealtimeTicketResponse {
  ticket: string;
  expires_in_seconds: number;
}


export interface ChannelRealtimeResumeRequest {
  after_sequence: number;
  limit?: number;
}


export interface ChannelRealtimeEventPage {
  items: ChannelRealtimeEvent[];
  current_sequence: number;
}


export interface ChannelRealtimeActionResponse {
  accepted: boolean;
}


export interface ChannelRealtimeTypingPayload {
  user_id?: string;
  typing?: boolean;
}


export interface ChannelRealtimePresencePayload {
  user_id?: string;
  state?: ChannelPresenceState;
}


export interface ChannelRealtimeMessagePayload {
  id: string;
  channel_id: string;
  sender_user_id: string | null;
  message_type: "text" | "system";
  content: string;
  edited_at: string | null;
  deleted_at: string | null;
  created_at: string;
}


export interface ChannelRealtimeAttachmentPayload {
  message_id: string;
  channel_id: string;
  attachment_ids: string[];
}


export interface ChannelRealtimeSocketHeartbeat {
  action: "heartbeat";
}


export interface ChannelRealtimeSocketTypingStart {
  action: "typing.start";
}


export interface ChannelRealtimeSocketTypingStop {
  action: "typing.stop";
}


export type ChannelRealtimeSocketAction =
  | ChannelRealtimeSocketHeartbeat
  | ChannelRealtimeSocketTypingStart
  | ChannelRealtimeSocketTypingStop;


export type ChannelRealtimeConnectionState =
  | "idle"
  | "connecting"
  | "connected"
  | "reconnecting"
  | "disconnected"
  | "error";