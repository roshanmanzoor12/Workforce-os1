import {
  api,
} from "@/lib/api/client";

import type {
  CreateWorkspaceInvitationRequest,
  WorkspaceInvitationActionResponse,
  WorkspaceInvitationListResponse,
  WorkspaceInvitationSecretResponse,
  WorkspaceInvitationTokenPublic,
  IncomingWorkspaceInvitationsResponse,
} from "@/types/workspace-invitations";


async function create(
  workspaceId:
    string,

  payload:
    CreateWorkspaceInvitationRequest,
): Promise<WorkspaceInvitationSecretResponse> {
  return api.post<WorkspaceInvitationSecretResponse>(
    `/workspaces/${workspaceId}/invitations`,
    payload,
  );
}


async function list(
  workspaceId:
    string,
): Promise<WorkspaceInvitationListResponse> {
  const response =
    await api.get<WorkspaceInvitationListResponse>(
      `/workspaces/${workspaceId}/invitations`,
    );


  return {
    ...response,

    items:
      Array.isArray(
        response.items,
      )
        ? response.items
        : [],
  };
}


async function resend(
  workspaceId:
    string,

  invitationId:
    string,
): Promise<WorkspaceInvitationSecretResponse> {
  return api.post<WorkspaceInvitationSecretResponse>(
    `/workspaces/${workspaceId}/invitations/${invitationId}/resend`,
    {},
  );
}


async function revoke(
  workspaceId:
    string,

  invitationId:
    string,
): Promise<WorkspaceInvitationActionResponse> {
  return api.delete<WorkspaceInvitationActionResponse>(
    `/workspaces/${workspaceId}/invitations/${invitationId}`,
  );
}


async function getByToken(
  token:
    string,
): Promise<WorkspaceInvitationTokenPublic> {
  return api.get<WorkspaceInvitationTokenPublic>(
    `/workspace-invitations/${encodeURIComponent(
      token,
    )}`,
  );
}


async function accept(
  token:
    string,
): Promise<WorkspaceInvitationActionResponse> {
  return api.post<WorkspaceInvitationActionResponse>(
    `/workspace-invitations/${encodeURIComponent(
      token,
    )}/accept`,
    {},
  );
}


async function decline(
  token:
    string,
): Promise<WorkspaceInvitationActionResponse> {
  return api.post<WorkspaceInvitationActionResponse>(
    `/workspace-invitations/${encodeURIComponent(
      token,
    )}/decline`,
    {},
  );
}


async function incoming(): Promise<IncomingWorkspaceInvitationsResponse> {
  return api.get<IncomingWorkspaceInvitationsResponse>("/workspace-invitations/incoming");
}

async function respondToIncoming(invitationId: string, action: "accept" | "decline"): Promise<WorkspaceInvitationActionResponse> {
  return api.post<WorkspaceInvitationActionResponse>(`/workspace-invitations/incoming/${encodeURIComponent(invitationId)}/${action}`, {});
}

export const workspaceInvitationsService = {
  incoming,
  respondToIncoming,
  create,

  list,

  resend,

  revoke,

  getByToken,

  accept,

  decline,
};
