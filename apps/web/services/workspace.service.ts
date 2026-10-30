import {
  api,
} from "@/lib/api/client";

import type {
  WorkspaceDetailResponse,
  WorkspaceListResponse,
  WorkspacePublic,
  WorkspaceMembershipPublic,
  TenantDatabasePublic,
} from "@/types/workspace";

export interface WorkspaceCreateRequest {
  name:
    string;

  slug?:
    string | null;

  timezone?:
    string;

  logo_url?:
    string | null;
}

export interface WorkspaceCreateResponse {
  message:
    string;

  workspace:
    WorkspacePublic;

  membership:
    WorkspaceMembershipPublic;

  tenant:
    TenantDatabasePublic | null;
}

async function list():
  Promise<WorkspaceListResponse> {
  return api.get<WorkspaceListResponse>(
    "/workspaces",
  );
}

async function get(
  workspaceId: string,
): Promise<WorkspaceDetailResponse> {
  return api.get<WorkspaceDetailResponse>(
    `/workspaces/${workspaceId}`,
  );
}

async function create(
  payload:
    WorkspaceCreateRequest,
): Promise<WorkspaceCreateResponse> {
  return api.post<WorkspaceCreateResponse>(
    "/workspaces",
    payload,
  );
}

async function provision(
  workspaceId: string,
): Promise<unknown> {
  return api.post(
    `/workspaces/${workspaceId}/provision`,
  );
}

export const workspaceService = {
  list,
  get,
  create,
  provision,
};