import {
  api,
} from "@/lib/api/client";

import type {
  WorkspaceBootstrapResponse,
} from "@/types/workspace-access";

async function getBootstrap(
  workspaceId: string,
): Promise<WorkspaceBootstrapResponse> {
  const [bootstrap, billing] = await Promise.all([
    api.get<WorkspaceBootstrapResponse>(
      `/workspaces/${workspaceId}/bootstrap`,
    ),
    api.get<NonNullable<WorkspaceBootstrapResponse["billing"]>>(
      `/billing/workspaces/${workspaceId}/status`,
    ),
  ]);

  return { ...bootstrap, billing };
}

export const workspaceAccessService = {
  getBootstrap,
};
