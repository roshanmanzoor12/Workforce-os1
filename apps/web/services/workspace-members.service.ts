import {
  api,
} from "@/lib/api/client";

import type {
  UpdateWorkspaceMemberRoleRequest,
  WorkspaceMemberActionResponse,
  WorkspaceMemberPublic,
  WorkspaceMembersResponse,
  WorkspaceMemberVisibilityRequest,
} from "@/types/workspace-members";


async function list(
  workspaceId:
    string,
): Promise<WorkspaceMembersResponse> {
  return api.get<WorkspaceMembersResponse>(
    `/workspaces/${workspaceId}/members`,
  );
}


async function updateRole(
  workspaceId:
    string,

  membershipId:
    string,

  payload:
    UpdateWorkspaceMemberRoleRequest,
): Promise<WorkspaceMemberPublic> {
  return api.patch<WorkspaceMemberPublic>(
    `/workspaces/${workspaceId}/members/${membershipId}/role`,
    payload,
  );
}


async function kick(
  workspaceId:
    string,

  membershipId:
    string,
): Promise<WorkspaceMemberActionResponse> {
  return api.post<WorkspaceMemberActionResponse>(
    `/workspaces/${workspaceId}/members/${membershipId}/kick`,
  );
}


async function ban(
  workspaceId:
    string,

  membershipId:
    string,
): Promise<WorkspaceMemberActionResponse> {
  return api.post<WorkspaceMemberActionResponse>(
    `/workspaces/${workspaceId}/members/${membershipId}/ban`,
  );
}


async function mute(
  workspaceId:
    string,

  membershipId:
    string,
): Promise<WorkspaceMemberActionResponse> {
  return api.post<WorkspaceMemberActionResponse>(
    `/workspaces/${workspaceId}/members/${membershipId}/mute`,
  );
}


async function deafen(
  workspaceId:
    string,

  membershipId:
    string,
): Promise<WorkspaceMemberActionResponse> {
  return api.post<WorkspaceMemberActionResponse>(
    `/workspaces/${workspaceId}/members/${membershipId}/deafen`,
  );
}


async function updateVisibility(
  workspaceId:
    string,

  membershipId:
    string,

  hidden:
    boolean,
): Promise<WorkspaceMemberActionResponse> {
  const payload:
    WorkspaceMemberVisibilityRequest = {
      hidden,
    };


  return api.patch<WorkspaceMemberActionResponse>(
    `/workspaces/${workspaceId}/members/${membershipId}/visibility`,
    payload,
  );
}


export const workspaceMembersService = {
  list,

  updateRole,

  kick,

  ban,

  mute,

  deafen,

  updateVisibility,
};