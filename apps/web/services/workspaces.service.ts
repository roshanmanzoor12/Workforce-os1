import { api } from "@/lib/api/client";

import type {
  WorkspaceDetailResponse,
  WorkspaceListResponse,
} from "@/types/workspace";

export const workspacesService = {
  list() {
    return api.get<WorkspaceListResponse>(
      "/workspaces",
    );
  },

  get(workspaceId: string) {
    return api.get<WorkspaceDetailResponse>(
      `/workspaces/${workspaceId}`,
    );
  },

  create(payload: {
    name: string;
    workspace_type?: "company" | "agency";
    slug?: string | null;
    timezone?: string;
    logo_url?: string | null;
  }) {
    return api.post<{
      message: string;
      workspace:
        WorkspaceDetailResponse["workspace"];
      membership:
        WorkspaceDetailResponse["membership"];
      tenant:
        WorkspaceDetailResponse["tenant"];
    }>(
      "/workspaces",
      payload,
    );
  },

  update(
    workspaceId: string,
    payload: {
      name?: string | null;
      workspace_type?: "company" | "agency";
      timezone?: string | null;
      logo_url?: string | null;
      primary_color?: string;
      accent_color?: string;
    },
  ) {
    return api.patch<WorkspaceDetailResponse>(
      `/workspaces/${workspaceId}`,
      payload,
    );
  },

  provision(workspaceId: string) {
    return api.post<{
      workspace_id: string;
      cluster_key: string;
      schema_version: string;
      database_created: boolean;
      database_already_existed: boolean;
      metadata_created: boolean;
      workspace_ready: boolean;
      tenant_ready: boolean;
    }>(
      `/workspaces/${workspaceId}/provision`,
    );
  },

  retryProvisioning(
    workspaceId: string,
  ) {
    return api.post(
      `/workspaces/${workspaceId}/retry-provisioning`,
    );
  },

  suspend(workspaceId: string) {
    return api.post(
      `/workspaces/${workspaceId}/suspend`,
    );
  },

  archive(workspaceId: string) {
    return api.post(
      `/workspaces/${workspaceId}/archive`,
    );
  },

  updateMembershipRole(
    workspaceId: string,
    membershipId: string,
    role:
      | "owner"
      | "admin"
      | "member",
  ) {
    return api.patch(
      `/workspaces/${workspaceId}/memberships/${membershipId}/role`,
      {
        role_key: role,
      },
    );
  },

  updateMembershipStatus(
    workspaceId: string,
    membershipId: string,
    status:
      | "active"
      | "invited"
      | "suspended"
      | "removed",
  ) {
    return api.patch(
      `/workspaces/${workspaceId}/memberships/${membershipId}/status`,
      {
        status,
      },
    );
  },

  removeMembership(
    workspaceId: string,
    membershipId: string,
  ) {
    return api.delete<{
      message: string;
      success: boolean;
    }>(
      `/workspaces/${workspaceId}/memberships/${membershipId}`,
    );
  },
};