import { api } from "@/lib/api/client";

/** Send before /auth/logout while the browser bearer token is still usable. */
export async function endLiveScreenLoginOnLogout(workspaceId: string): Promise<void> {
  await api.post(`/workspaces/${workspaceId}/live-monitoring/auto-flow/stop`, {});
}
