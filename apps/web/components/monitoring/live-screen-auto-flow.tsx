"use client";

import { useEffect } from "react";
import { useWorkspace } from "@/contexts/workspace-context";
import { getAuthSession } from "@/lib/auth/session";
import { api } from "@/lib/api/client";

/** Keep an authenticated browser-workspace lease alive. UI for explicit future
 * screen-sharing approval lives inside Employee monitoring settings, not a
 * floating card. Browser refresh does not revoke; logout uses backend stop.
 */
export function LiveScreenAutoFlow() {
  const { workspaceId, mode, user } = useWorkspace();
  useEffect(() => {
    if (!workspaceId || !user || mode !== "workspace") return;
    let disposed = false;
    const ping = async () => {
      if (disposed || !getAuthSession()) return;
      try {
        await api.post(`/workspaces/${workspaceId}/live-monitoring/auto-flow/ping`, {});
      } catch {
        // Ping failures must not automatically create duplicate capture requests.
      }
    };
    void ping();
    const interval = window.setInterval(() => void ping(), 25000);
    return () => { disposed = true; window.clearInterval(interval); };
  }, [workspaceId, mode, user?.id]);
  return null;
}
