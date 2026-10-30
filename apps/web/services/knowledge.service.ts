import {
  api,
} from "@/lib/api/client";

import type {
  KnowledgeCreateRequest,
  KnowledgeListResponse,
  KnowledgePublic,
  KnowledgeUpdateRequest,
} from "@/types/knowledge";


async function listMine(
  workspaceId: string,
  includeArchived = false,
): Promise<KnowledgeListResponse> {
  return api.get<KnowledgeListResponse>(
    `/workspaces/${workspaceId}/knowledge/me`,
    {
      query: {
        include_archived:
          includeArchived,
      },
    },
  );
}


async function createMine(
  workspaceId: string,
  payload: KnowledgeCreateRequest,
): Promise<KnowledgePublic> {
  return api.post<KnowledgePublic>(
    `/workspaces/${workspaceId}/knowledge/me`,
    payload,
  );
}


async function updateMine(
  workspaceId: string,
  entryId: string,
  payload: KnowledgeUpdateRequest,
): Promise<KnowledgePublic> {
  return api.patch<KnowledgePublic>(
    `/workspaces/${workspaceId}/knowledge/me/${entryId}`,
    payload,
  );
}


async function deleteMine(
  workspaceId: string,
  entryId: string,
): Promise<void> {
  await api.delete<void>(
    `/workspaces/${workspaceId}/knowledge/me/${entryId}`,
  );
}


async function listWorkspace(
  workspaceId: string,
): Promise<KnowledgeListResponse> {
  return api.get<KnowledgeListResponse>(
    `/workspaces/${workspaceId}/knowledge/workspace`,
  );
}


async function get(
  workspaceId: string,
  entryId: string,
): Promise<KnowledgePublic> {
  return api.get<KnowledgePublic>(
    `/workspaces/${workspaceId}/knowledge/${entryId}`,
  );
}


export const knowledgeService = {
  listMine,

  createMine,

  updateMine,

  deleteMine,

  listWorkspace,

  get,
};