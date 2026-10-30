export type CallKind =
  | "VOICE"
  | "VIDEO";


export type CallScope =
  | "CONVERSATION"
  | "CHANNEL";


export type CallStatus =
  | "RINGING"
  | "ACTIVE"
  | "ENDED"
  | "CANCELLED";


export type CallParticipantState =
  | "INVITED"
  | "JOINED"
  | "LEFT"
  | "DECLINED";


export type ScreenShareState =
  | "STOPPED"
  | "ACTIVE";


export type CallSignalType =
  | "OFFER"
  | "ANSWER"
  | "ICE_CANDIDATE";


export interface CallParticipantResponse {
  user_id: string;

  state: CallParticipantState;

  microphone_enabled: boolean;

  camera_enabled: boolean;

  screen_share_state: ScreenShareState;

  joined_at: string | null;

  left_at: string | null;
}


export interface CallParticipantsResponse {
  call_id: string;

  participants: CallParticipantResponse[];
}


export interface CallResponse {
  id: string;

  scope: CallScope;

  conversation_id: string | null;

  channel_id: string | null;

  started_by_user_id: string;

  kind: CallKind;

  status: CallStatus;

  created_at: string;

  started_at: string | null;

  ended_at: string | null;

  participants?: CallParticipantResponse[];
}


export interface CreateCallRequest {
  scope: CallScope;

  kind: CallKind;

  conversation_id?: string | null;

  channel_id?: string | null;

  invited_user_ids?: string[];
}


export interface CallSignalRequest {
  signal_type: CallSignalType;

  target_user_id?: string | null;

  payload: Record<string, unknown>;
}


export interface CallSignalResponse {
  event: Record<string, unknown>;
}