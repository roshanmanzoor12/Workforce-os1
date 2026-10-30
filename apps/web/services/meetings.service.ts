import {
  api,
} from "@/lib/api/client";

import type {
  MeetingCreateRequest,
  MeetingDetailResponse,
  MeetingInvitationListResponse,
  MeetingListResponse,
  MeetingParticipantAddRequest,
  MeetingParticipantResponse,
  MeetingParticipantStatus,
  MeetingResponse,
  MeetingSelfResponse,
  MeetingUpdateRequest,
} from "@/types/meetings";


async function list(
  workspaceId: string,
): Promise<MeetingListResponse> {
  const response =
    await api.get<MeetingListResponse>(
      `/workspaces/${workspaceId}/meetings`,
    );


  return {
    ...response,

    meetings:
      response.meetings ??
      [],
  };
}


async function create(
  workspaceId: string,
  payload: MeetingCreateRequest,
): Promise<MeetingResponse> {
  return api.post<MeetingResponse>(
    `/workspaces/${workspaceId}/meetings`,
    payload,
  );
}


async function get(
  workspaceId: string,
  meetingId: string,
): Promise<MeetingDetailResponse> {
  const response =
    await api.get<MeetingDetailResponse>(
      `/workspaces/${workspaceId}/meetings/${meetingId}`,
    );


  return {
    ...response,

    participants:
      response.participants ??
      [],
  };
}


async function update(
  workspaceId: string,
  meetingId: string,
  payload: MeetingUpdateRequest,
): Promise<MeetingResponse> {
  return api.patch<MeetingResponse>(
    `/workspaces/${workspaceId}/meetings/${meetingId}`,
    payload,
  );
}


async function start(
  workspaceId: string,
  meetingId: string,
): Promise<MeetingResponse> {
  return api.post<MeetingResponse>(
    `/workspaces/${workspaceId}/meetings/${meetingId}/start`,
    {},
  );
}


async function end(
  workspaceId: string,
  meetingId: string,
): Promise<MeetingResponse> {
  return api.post<MeetingResponse>(
    `/workspaces/${workspaceId}/meetings/${meetingId}/end`,
    {},
  );
}


async function cancel(
  workspaceId: string,
  meetingId: string,
): Promise<MeetingResponse> {
  return api.post<MeetingResponse>(
    `/workspaces/${workspaceId}/meetings/${meetingId}/cancel`,
    {},
  );
}


async function addParticipant(
  workspaceId: string,
  meetingId: string,
  payload: MeetingParticipantAddRequest,
): Promise<MeetingParticipantResponse> {
  return api.post<MeetingParticipantResponse>(
    `/workspaces/${workspaceId}/meetings/${meetingId}/participants`,
    payload,
  );
}


async function updateParticipantStatus(
  workspaceId: string,
  meetingId: string,
  employeeId: string,
  status: MeetingParticipantStatus,
): Promise<MeetingParticipantResponse> {
  return api.patch<MeetingParticipantResponse>(
    `/workspaces/${workspaceId}/meetings/${meetingId}/participants/${employeeId}/status`,
    {
      status,
    },
  );
}


async function removeParticipant(
  workspaceId: string,
  meetingId: string,
  employeeId: string,
): Promise<void> {
  await api.delete<void>(
    `/workspaces/${workspaceId}/meetings/${meetingId}/participants/${employeeId}`,
  );
}


async function listMyInvitations(
  workspaceId: string,
): Promise<MeetingInvitationListResponse> {
  const response =
    await api.get<MeetingInvitationListResponse>(
      `/workspaces/${workspaceId}/meetings/me/invitations`,
    );


  return {
    ...response,

    invitations:
      response.invitations ??
      [],
  };
}


async function respondToInvitation(
  workspaceId: string,
  meetingId: string,
  status: MeetingParticipantStatus,
): Promise<MeetingSelfResponse> {
  return api.patch<MeetingSelfResponse>(
    `/workspaces/${workspaceId}/meetings/me/${meetingId}/response`,
    {
      status,
    },
  );
}


export const meetingsService = {
  list,

  create,

  get,

  update,

  start,

  end,

  cancel,

  addParticipant,

  updateParticipantStatus,

  removeParticipant,

  listMyInvitations,

  respondToInvitation,
};