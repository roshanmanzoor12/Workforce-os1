import {
  api,
} from "@/lib/api/client";


/* -------------------------------------------------------------------------- */
/* Channel types                                                               */
/* -------------------------------------------------------------------------- */

export type WorkspaceChannelType =
  | "text"
  | "announcement"
  | "voice";


export type WorkspaceChannelMessageType =
  | "text"
  | "system";


export interface WorkspaceChannelPublic {
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


export interface WorkspaceChannelCreateRequest {
  workspace_id: string;

  name: string;

  channel_type?: WorkspaceChannelType;
}


export interface WorkspaceChannelUpdateRequest {
  name: string;
}


export interface WorkspaceChannelMessagePublic {
  id: string;

  channel_id: string;

  sender_user_id: string | null;

  message_type: WorkspaceChannelMessageType;

  content: string;

  edited_at: string | null;

  deleted_at: string | null;

  created_at: string;
}


export interface WorkspaceChannelMessageCreateRequest {
  content: string;
}


/* -------------------------------------------------------------------------- */
/* Voice types                                                                 */
/* -------------------------------------------------------------------------- */

export type VoicePresenceState =
  | "connected"
  | "disconnected";


export type VoiceSignalType =
  | "offer"
  | "answer"
  | "ice_candidate"
  | "renegotiate";


export interface VoiceParticipantPublic {
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


export interface VoiceCallPublic {
  id: string;

  channel_id: string;

  created_by_user_id: string;

  status: string;

  created_at: string;

  ended_at: string | null;

  participants?: VoiceParticipantPublic[];
}


export interface VoiceJoinResponse {
  call: VoiceCallPublic;

  participant: VoiceParticipantPublic;
}


export interface VoiceParticipantListResponse {
  call_id: string;

  participants?: VoiceParticipantPublic[];
}


export interface VoiceSelfStateRequest {
  self_muted?: boolean | null;

  self_deafened?: boolean | null;
}


export interface VoiceModeratorStateRequest {
  server_muted?: boolean | null;

  server_deafened?: boolean | null;
}


export interface VoiceModerationReasonRequest {
  reason?: string | null;
}


export interface VoiceBanResponse {
  channel_id: string;

  user_id: string;

  is_active: boolean;

  reason: string | null;
}


export interface VoiceScreenShareResponse {
  participant: VoiceParticipantPublic;
}


export interface VoiceSignalRequest {
  signal_type: VoiceSignalType;

  target_user_id?: string | null;

  payload: Record<string, unknown>;
}


export interface VoiceSignalEnvelope {
  event_id: string;

  call_id: string;

  channel_id: string;

  sender_user_id: string;

  target_user_id: string | null;

  signal_type: VoiceSignalType;

  payload: Record<string, unknown>;

  created_at: string;
}


export interface VoiceSignalResponse {
  event: VoiceSignalEnvelope;
}


export interface VoiceSignalPollResponse {
  events?: VoiceSignalEnvelope[];
}


export interface VoicePresenceHeartbeatRequest {
  connection_id: string;
}


export interface VoiceSpeakingRequest {
  speaking: boolean;
}


export interface VoiceRealtimeStateResponse {
  call_id: string;

  user_id: string;

  presence: VoicePresenceState;

  speaking: boolean;
}


export interface VoiceCapabilitiesResponse {
  voice_channels?: boolean;

  single_active_call_per_channel?: boolean;

  self_mute?: boolean;

  self_deafen?: boolean;

  moderator_mute?: boolean;

  moderator_deafen?: boolean;

  kick?: boolean;

  ban?: boolean;

  screen_share?: boolean;

  webrtc_signaling?: boolean;

  presence?: boolean;

  speaking_state?: boolean;
}


/* -------------------------------------------------------------------------- */
/* Channels                                                                    */
/* -------------------------------------------------------------------------- */

async function list(
  workspaceId: string,
): Promise<WorkspaceChannelPublic[]> {
  return api.get<WorkspaceChannelPublic[]>(
    `/workspace-channels/workspace/${workspaceId}`,
  );
}


async function create(
  payload: WorkspaceChannelCreateRequest,
): Promise<WorkspaceChannelPublic> {
  return api.post<WorkspaceChannelPublic>(
    "/workspace-channels",
    payload,
  );
}


async function rename(
  channelId: string,

  payload: WorkspaceChannelUpdateRequest,
): Promise<WorkspaceChannelPublic> {
  return api.patch<WorkspaceChannelPublic>(
    `/workspace-channels/${channelId}`,
    payload,
  );
}


async function archive(
  channelId: string,
): Promise<void> {
  await api.delete<void>(
    `/workspace-channels/${channelId}`,
  );
}


/* -------------------------------------------------------------------------- */
/* Messages                                                                    */
/* -------------------------------------------------------------------------- */

async function listMessages(
  channelId: string,

  limit =
    100,
): Promise<WorkspaceChannelMessagePublic[]> {
  return api.get<WorkspaceChannelMessagePublic[]>(
    `/workspace-channels/${channelId}/messages`,
    {
      query: {
        limit,
      },
    },
  );
}


async function sendMessage(
  channelId: string,

  payload: WorkspaceChannelMessageCreateRequest,
): Promise<WorkspaceChannelMessagePublic> {
  return api.post<WorkspaceChannelMessagePublic>(
    `/workspace-channels/${channelId}/messages`,
    payload,
  );
}


/* -------------------------------------------------------------------------- */
/* Voice                                                                       */
/* -------------------------------------------------------------------------- */

async function getActiveVoiceCall(
  workspaceId: string,

  channelId: string,
): Promise<VoiceCallPublic> {
  return api.get<VoiceCallPublic>(
    `/workspaces/${workspaceId}/channels/${channelId}/voice/active-call`,
  );
}


async function joinVoice(
  workspaceId: string,

  channelId: string,
): Promise<VoiceJoinResponse> {
  return api.post<VoiceJoinResponse>(
    `/workspaces/${workspaceId}/channels/${channelId}/voice/join`,
    {},
  );
}


async function leaveVoice(
  workspaceId: string,

  channelId: string,
): Promise<VoiceParticipantPublic> {
  return api.post<VoiceParticipantPublic>(
    `/workspaces/${workspaceId}/channels/${channelId}/voice/leave`,
    {},
  );
}


async function listVoiceParticipants(
  workspaceId: string,

  channelId: string,
): Promise<VoiceParticipantListResponse> {
  const response =
    await api.get<VoiceParticipantListResponse>(
      `/workspaces/${workspaceId}/channels/${channelId}/voice/participants`,
    );


  return {
    ...response,

    participants:
      response.participants ??
      [],
  };
}


async function updateSelfVoiceState(
  workspaceId: string,

  channelId: string,

  payload: VoiceSelfStateRequest,
): Promise<VoiceParticipantPublic> {
  return api.patch<VoiceParticipantPublic>(
    `/workspaces/${workspaceId}/channels/${channelId}/voice/me`,
    payload,
  );
}


async function moderateVoiceParticipant(
  workspaceId: string,

  channelId: string,

  userId: string,

  payload: VoiceModeratorStateRequest,
): Promise<VoiceParticipantPublic> {
  return api.patch<VoiceParticipantPublic>(
    `/workspaces/${workspaceId}/channels/${channelId}/voice/participants/${userId}/moderation`,
    payload,
  );
}


async function kickVoiceParticipant(
  workspaceId: string,

  channelId: string,

  userId: string,
): Promise<VoiceParticipantPublic> {
  return api.post<VoiceParticipantPublic>(
    `/workspaces/${workspaceId}/channels/${channelId}/voice/participants/${userId}/kick`,
    {},
  );
}


async function banVoiceUser(
  workspaceId: string,

  channelId: string,

  userId: string,

  payload: VoiceModerationReasonRequest = {},
): Promise<VoiceBanResponse> {
  return api.post<VoiceBanResponse>(
    `/workspaces/${workspaceId}/channels/${channelId}/voice/bans/${userId}`,
    payload,
  );
}


async function unbanVoiceUser(
  workspaceId: string,

  channelId: string,

  userId: string,
): Promise<VoiceBanResponse> {
  return api.delete<VoiceBanResponse>(
    `/workspaces/${workspaceId}/channels/${channelId}/voice/bans/${userId}`,
  );
}


async function startVoiceScreenShare(
  workspaceId: string,

  channelId: string,
): Promise<VoiceScreenShareResponse> {
  return api.post<VoiceScreenShareResponse>(
    `/workspaces/${workspaceId}/channels/${channelId}/voice/screen-share/start`,
    {},
  );
}


async function stopVoiceScreenShare(
  workspaceId: string,

  channelId: string,
): Promise<VoiceScreenShareResponse> {
  return api.post<VoiceScreenShareResponse>(
    `/workspaces/${workspaceId}/channels/${channelId}/voice/screen-share/stop`,
    {},
  );
}


async function sendVoiceSignal(
  workspaceId: string,

  channelId: string,

  payload: VoiceSignalRequest,
): Promise<VoiceSignalResponse> {
  return api.post<VoiceSignalResponse>(
    `/workspaces/${workspaceId}/channels/${channelId}/voice/signal`,
    payload,
  );
}


async function pollVoiceSignals(
  workspaceId: string,

  channelId: string,
): Promise<VoiceSignalPollResponse> {
  const response =
    await api.get<VoiceSignalPollResponse>(
      `/workspaces/${workspaceId}/channels/${channelId}/voice/signals`,
    );


  return {
    ...response,

    events:
      response.events ??
      [],
  };
}


async function voicePresenceHeartbeat(
  workspaceId: string,

  channelId: string,

  payload: VoicePresenceHeartbeatRequest,
): Promise<VoiceRealtimeStateResponse> {
  return api.post<VoiceRealtimeStateResponse>(
    `/workspaces/${workspaceId}/channels/${channelId}/voice/presence`,
    payload,
  );
}


async function setVoiceSpeaking(
  workspaceId: string,

  channelId: string,

  payload: VoiceSpeakingRequest,
): Promise<VoiceRealtimeStateResponse> {
  return api.post<VoiceRealtimeStateResponse>(
    `/workspaces/${workspaceId}/channels/${channelId}/voice/speaking`,
    payload,
  );
}


async function voiceCapabilities(
  workspaceId: string,

  channelId: string,
): Promise<VoiceCapabilitiesResponse> {
  return api.get<VoiceCapabilitiesResponse>(
    `/workspaces/${workspaceId}/channels/${channelId}/voice/capabilities`,
  );
}


export const workspaceChannelsService = {
  list,

  create,

  rename,

  archive,

  listMessages,

  sendMessage,

  getActiveVoiceCall,

  joinVoice,

  leaveVoice,

  listVoiceParticipants,

  updateSelfVoiceState,

  moderateVoiceParticipant,

  kickVoiceParticipant,

  banVoiceUser,

  unbanVoiceUser,

  startVoiceScreenShare,

  stopVoiceScreenShare,

  sendVoiceSignal,

  pollVoiceSignals,

  voicePresenceHeartbeat,

  setVoiceSpeaking,

  voiceCapabilities,
};