export type WorkspaceChannelType =
  | "text"
  | "announcement"
  | "voice";


export type WorkspaceChannelMessageType =
  | "text"
  | "system";


export interface WorkspaceChannel {
  id: string;
  workspace_id: string;
  name: string;
  slug: string;
  channel_type: WorkspaceChannelType;
  created_by_user_id: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}


export interface WorkspaceChannelMessage {
  id: string;
  channel_id: string;
  sender_user_id: string | null;
  message_type: WorkspaceChannelMessageType;
  content: string;
  edited_at: string | null;
  deleted_at: string | null;
  created_at: string;
}


export interface WorkspaceChannelCreatePayload {
  workspace_id: string;
  name: string;
  channel_type?: WorkspaceChannelType;
}


export interface WorkspaceChannelUpdatePayload {
  name: string;
}


/* =========================================================
   VOICE
========================================================= */

export type VoicePresenceState =
  | "connected"
  | "disconnected";


export type VoiceSignalType =
  | "offer"
  | "answer"
  | "ice_candidate"
  | "renegotiate";


export interface VoiceParticipant {
  id: string;
  call_id: string;
  user_id: string;
  state: string;

  self_muted: boolean;
  self_deafened: boolean;

  server_muted: boolean;
  server_deafened: boolean;

  effective_muted: boolean;
  effective_deafened: boolean;

  screen_sharing: boolean;

  presence: VoicePresenceState;

  speaking: boolean;

  joined_at: string;

  left_at: string | null;
}


export interface VoiceCall {
  id: string;
  channel_id: string;
  created_by_user_id: string;
  status: string;
  created_at: string;
  ended_at: string | null;
  participants: VoiceParticipant[];
}


export interface VoiceJoinResponse {
  call: VoiceCall;
  participant: VoiceParticipant;
}


export interface VoiceParticipantListResponse {
  call_id: string;
  participants: VoiceParticipant[];
}


export interface VoiceScreenShareResponse {
  participant: VoiceParticipant;
}


export interface VoiceRealtimeStateResponse {
  call_id: string;
  user_id: string;
  presence: VoicePresenceState;
  speaking: boolean;
}


export interface VoiceSignalEnvelope {
  event_id: string;
  call_id: string;
  channel_id: string;
  sender_user_id: string;

  target_user_id:
    | string
    | null;

  signal_type: VoiceSignalType;

  payload: Record<
    string,
    unknown
  >;

  created_at: string;
}


export interface VoiceSignalResponse {
  event: VoiceSignalEnvelope;
}


export interface VoiceSignalPollResponse {
  events: VoiceSignalEnvelope[];
}


export interface VoiceCapabilities {
  voice_channels: boolean;

  single_active_call_per_channel:
    boolean;

  self_mute: boolean;
  self_deafen: boolean;

  moderator_mute: boolean;
  moderator_deafen: boolean;

  kick: boolean;
  ban: boolean;

  screen_share: boolean;
  webrtc_signaling: boolean;

  presence: boolean;
  speaking_state: boolean;
}