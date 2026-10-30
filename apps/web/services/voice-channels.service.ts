import {
  api,
} from "@/lib/api/client";

import type {
  VoiceCall,
  VoiceCapabilities,
  VoiceJoinResponse,
  VoiceParticipant,
  VoiceParticipantListResponse,
  VoiceRealtimeStateResponse,
  VoiceScreenShareResponse,
  VoiceSignalPollResponse,
  VoiceSignalResponse,
  VoiceSignalType,
} from "@/types/channels";


function base(
  workspaceId: string,
  channelId: string,
): string {
  return (
    `/workspaces/${workspaceId}` +
    `/channels/${channelId}/voice`
  );
}


async function activeCall(
  workspaceId: string,
  channelId: string,
): Promise<VoiceCall> {
  return api.get<VoiceCall>(
    `${base(
      workspaceId,
      channelId,
    )}/active-call`,
  );
}


async function join(
  workspaceId: string,
  channelId: string,
): Promise<VoiceJoinResponse> {
  return api.post<VoiceJoinResponse>(
    `${base(
      workspaceId,
      channelId,
    )}/join`,
    {},
  );
}


async function leave(
  workspaceId: string,
  channelId: string,
): Promise<VoiceParticipant> {
  return api.post<VoiceParticipant>(
    `${base(
      workspaceId,
      channelId,
    )}/leave`,
    {},
  );
}


async function participants(
  workspaceId: string,
  channelId: string,
): Promise<VoiceParticipantListResponse> {
  return api.get<VoiceParticipantListResponse>(
    `${base(
      workspaceId,
      channelId,
    )}/participants`,
  );
}


async function updateSelf(
  workspaceId: string,
  channelId: string,
  payload: {
    self_muted?: boolean;
    self_deafened?: boolean;
  },
): Promise<VoiceParticipant> {
  return api.patch<VoiceParticipant>(
    `${base(
      workspaceId,
      channelId,
    )}/me`,
    payload,
  );
}


async function moderate(
  workspaceId: string,
  channelId: string,
  userId: string,
  payload: {
    server_muted?: boolean;
    server_deafened?: boolean;
  },
): Promise<VoiceParticipant> {
  return api.patch<VoiceParticipant>(
    `${base(
      workspaceId,
      channelId,
    )}/participants/${userId}/moderation`,
    payload,
  );
}


async function kick(
  workspaceId: string,
  channelId: string,
  userId: string,
): Promise<VoiceParticipant> {
  return api.post<VoiceParticipant>(
    `${base(
      workspaceId,
      channelId,
    )}/participants/${userId}/kick`,
    {},
  );
}


async function ban(
  workspaceId: string,
  channelId: string,
  userId: string,
  reason?: string,
) {
  return api.post<{
    channel_id: string;
    user_id: string;
    is_active: boolean;
    reason: string | null;
  }>(
    `${base(
      workspaceId,
      channelId,
    )}/bans/${userId}`,
    {
      reason:
        reason ?? null,
    },
  );
}


async function unban(
  workspaceId: string,
  channelId: string,
  userId: string,
) {
  return api.delete<{
    channel_id: string;
    user_id: string;
    is_active: boolean;
    reason: string | null;
  }>(
    `${base(
      workspaceId,
      channelId,
    )}/bans/${userId}`,
  );
}


async function startScreenShare(
  workspaceId: string,
  channelId: string,
): Promise<VoiceScreenShareResponse> {
  return api.post<VoiceScreenShareResponse>(
    `${base(
      workspaceId,
      channelId,
    )}/screen-share/start`,
    {},
  );
}


async function stopScreenShare(
  workspaceId: string,
  channelId: string,
): Promise<VoiceScreenShareResponse> {
  return api.post<VoiceScreenShareResponse>(
    `${base(
      workspaceId,
      channelId,
    )}/screen-share/stop`,
    {},
  );
}


async function signal(
  workspaceId: string,
  channelId: string,
  payload: {
    signal_type: VoiceSignalType;
    target_user_id?: string | null;

    payload: Record<
      string,
      unknown
    >;
  },
): Promise<VoiceSignalResponse> {
  return api.post<VoiceSignalResponse>(
    `${base(
      workspaceId,
      channelId,
    )}/signal`,
    payload,
  );
}


async function pollSignals(
  workspaceId: string,
  channelId: string,
): Promise<VoiceSignalPollResponse> {
  return api.get<VoiceSignalPollResponse>(
    `${base(
      workspaceId,
      channelId,
    )}/signals`,
  );
}


async function heartbeat(
  workspaceId: string,
  channelId: string,
  connectionId: string,
): Promise<VoiceRealtimeStateResponse> {
  return api.post<VoiceRealtimeStateResponse>(
    `${base(
      workspaceId,
      channelId,
    )}/presence`,
    {
      connection_id:
        connectionId,
    },
  );
}


async function speaking(
  workspaceId: string,
  channelId: string,
  value: boolean,
): Promise<VoiceRealtimeStateResponse> {
  return api.post<VoiceRealtimeStateResponse>(
    `${base(
      workspaceId,
      channelId,
    )}/speaking`,
    {
      speaking:
        value,
    },
  );
}


async function capabilities(
  workspaceId: string,
  channelId: string,
): Promise<VoiceCapabilities> {
  return api.get<VoiceCapabilities>(
    `${base(
      workspaceId,
      channelId,
    )}/capabilities`,
  );
}


export const voiceChannelsService = {
  activeCall,
  join,
  leave,
  participants,
  updateSelf,
  moderate,
  kick,
  ban,
  unban,
  startScreenShare,
  stopScreenShare,
  signal,
  pollSignals,
  heartbeat,
  speaking,
  capabilities,
};