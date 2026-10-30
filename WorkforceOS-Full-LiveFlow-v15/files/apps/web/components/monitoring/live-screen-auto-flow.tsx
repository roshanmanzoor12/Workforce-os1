"use client";

import { useEffect, useState } from "react";
import { useWorkspace } from "@/contexts/workspace-context";
import { getAuthSession } from "@/lib/auth/session";
import { api } from "@/lib/api/client";

type PingResult = { state: string; session_id?: string };
type ApprovalResult = { granted: boolean };

/** Mounted in authenticated workspace layout, never on login page.
 * No pagehide revoke: page refresh must not stop sharing. If the browser closes
 * without logout, the backend 120-second lease expires and stops native frames.
 */
export function LiveScreenAutoFlow() {
  const { workspaceId, mode, user } = useWorkspace();
  const [saved, setSaved] = useState<boolean | null>(null);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  useEffect(() => {
    if (!workspaceId || !user || mode !== "workspace") return;
    let disposed = false;
    const base = `/workspaces/${workspaceId}/live-monitoring/auto-flow`;
    const ping = async () => {
      if (disposed || !getAuthSession()) return;
      try {
        await api.post<PingResult>(`${base}/ping`, {});
      } catch (error) {
        if (!disposed) console.warn("Live screen workspace lease heartbeat unavailable", error);
      }
    };
    void ping();
    const interval = window.setInterval(() => void ping(), 25000);
    void api.get<ApprovalResult>(`${base}/saved-approval`).then(
      data => { if (!disposed) setSaved(data.granted); },
      () => { if (!disposed) setSaved(null); },
    );
    return () => { disposed = true; window.clearInterval(interval); };
  }, [workspaceId, mode, user?.id]);

  const choose = async (granted: boolean) => {
    if (!workspaceId || busy) return;
    setBusy(true);
    setNotice("");
    try {
      const result = await api.request<ApprovalResult>(
        `/workspaces/${workspaceId}/live-monitoring/auto-flow/saved-approval`,
        { method: "PUT", body: JSON.stringify({ granted }), headers: { "Content-Type": "application/json" } },
      );
      setSaved(result.granted);
      setNotice(granted ? "Future live-screen auto-approval enabled. The desktop sharing indicator and Stop Sharing remain required." : "Future auto-approval revoked; current screen sharing is stopped.");
    } catch {
      setNotice("Unable to update screen-sharing approval.");
    } finally {
      setBusy(false);
    }
  };

  if (!workspaceId || !user || mode !== "workspace" || saved === null) return null;
  return (
    <section aria-label="Screen sharing automatic approval" style={{ position: "fixed", bottom: 10, right: 12, zIndex: 70, maxWidth: 330, background: "var(--background, #fff)", color: "var(--foreground, #111)", border: "1px solid #aaa", borderRadius: 8, padding: 10, fontSize: 12, boxShadow: "0 2px 8px #0002" }}>
      <strong>Live Screen Sharing — employee control</strong>
      <p style={{ margin: "6px 0" }}>Allow future owner live-screen requests to be accepted automatically <strong>only when</strong> WorkforceOS Companion shows the sharing indicator. You can stop sharing at any time in the Companion.</p>
      <button disabled={busy} onClick={() => void choose(!saved)} type="button" style={{ border: "1px solid currentColor", padding: "4px 9px", borderRadius: 4 }}>
        {saved ? "Revoke saved screen-sharing approval" : "Allow automatic screen-sharing approval"}
      </button>
      {notice && <p role="status">{notice}</p>}
    </section>
  );
}
