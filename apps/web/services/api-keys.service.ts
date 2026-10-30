import {
  api,
} from "@/lib/api/client";


import type {
  APIKeyCreateRequest,
  APIKeyCreateResponse,
  APIKeyPublic,
  APIKeyRotateResponse,
} from "@/types/api-keys";


async function list(
  workspaceId: string,
  limit = 100,
  offset = 0,
): Promise<APIKeyPublic[]> {
  return api.get<APIKeyPublic[]>(
    `/workspaces/${workspaceId}/api-keys`,
    {
      query: {
        limit,
        offset,
      },
    },
  );
}


async function get(
  workspaceId: string,
  keyId: string,
): Promise<APIKeyPublic> {
  return api.get<APIKeyPublic>(
    `/workspaces/${workspaceId}/api-keys/${keyId}`,
  );
}


async function create(
  workspaceId: string,
  payload: APIKeyCreateRequest,
): Promise<APIKeyCreateResponse> {
  return api.post<APIKeyCreateResponse>(
    `/workspaces/${workspaceId}/api-keys`,
    payload,
  );
}


async function revoke(
  workspaceId: string,
  keyId: string,
): Promise<APIKeyPublic> {
  return api.post<APIKeyPublic>(
    `/workspaces/${workspaceId}/api-keys/${keyId}/revoke`,
    {},
  );
}


async function rotate(
  workspaceId: string,
  keyId: string,
): Promise<APIKeyRotateResponse> {
  return api.post<APIKeyRotateResponse>(
    `/workspaces/${workspaceId}/api-keys/${keyId}/rotate`,
    {},
  );
}


export const apiKeysService = {
  list,

  get,

  create,

  revoke,

  rotate,
};