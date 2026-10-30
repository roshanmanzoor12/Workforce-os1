import {
  api,
} from "@/lib/api/client";

import type {
  CallParticipantResponse,
  CallParticipantsResponse,
  CallResponse,
  CallSignalRequest,
  CallSignalResponse,
  CreateCallRequest,
} from "@/types/conversation-call";


async function create(
  payload:
    CreateCallRequest,
): Promise<CallResponse> {
  return api.post<CallResponse>(
    "/calls",
    payload,
  );
}


async function get(
  callId:
    string,
): Promise<CallResponse> {
  return api.get<CallResponse>(
    `/calls/${callId}`,
  );
}


async function participants(
  callId:
    string,
): Promise<CallParticipantsResponse> {
  return api.get<CallParticipantsResponse>(
    `/calls/${callId}/participants`,
  );
}


async function join(
  callId:
    string,
): Promise<CallParticipantResponse> {
  return api.post<CallParticipantResponse>(
    `/calls/${callId}/join`,
    {},
  );
}


async function leave(
  callId:
    string,
): Promise<CallParticipantResponse> {
  return api.post<CallParticipantResponse>(
    `/calls/${callId}/leave`,
    {},
  );
}


async function decline(
  callId:
    string,
): Promise<CallParticipantResponse> {
  return api.post<CallParticipantResponse>(
    `/calls/${callId}/decline`,
    {},
  );
}


async function end(
  callId:
    string,
): Promise<CallResponse> {
  return api.post<CallResponse>(
    `/calls/${callId}/end`,
    {},
  );
}


async function startScreenShare(
  callId:
    string,
): Promise<CallParticipantResponse> {
  return api.post<CallParticipantResponse>(
    `/calls/${callId}/screen-share/start`,
    {},
  );
}


async function stopScreenShare(
  callId:
    string,
): Promise<CallParticipantResponse> {
  return api.post<CallParticipantResponse>(
    `/calls/${callId}/screen-share/stop`,
    {},
  );
}


async function signal(
  callId:
    string,

  payload:
    CallSignalRequest,
): Promise<CallSignalResponse> {
  return api.post<CallSignalResponse>(
    `/calls/${callId}/signal`,
    payload,
  );
}


async function createConversationCall(
  conversationId:
    string,

  kind:
    "VOICE" | "VIDEO",

  invitedUserIds:
    string[] = [],
): Promise<CallResponse> {
  return create({
    scope:
      "CONVERSATION",

    kind,

    conversation_id:
      conversationId,

    channel_id:
      null,

    invited_user_ids:
      invitedUserIds,
  });
}


export const conversationCallsService = {
  create,

  get,

  participants,

  join,

  leave,

  decline,

  end,

  startScreenShare,

  stopScreenShare,

  signal,

  createConversationCall,
};