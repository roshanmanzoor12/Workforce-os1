"use client";

import { useEffect, useState } from "react";
import { useWorkspace } from "@/contexts/workspace-context";
import { api } from "@/lib/api/client";

type SavedApproval = { granted: boolean };

/** Employee's separate, revocable consent for *future automatic approval*.
 * Generic monitoring disclosure or "Allow live-screen requests" does NOT
 * grant this permission. This control is shown within Monitoring Settings.
 */
export function SavedScreenSharingSetting() {
  const { workspaceId, user, mode } = useWorkspace();
  const [granted, setGranted] = useState<boolean | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!workspaceId || !user || mode !== "workspace") { setGranted(null); return; }
    let cancelled = false;
    setGranted(null);
    setError("");
    void api.get<SavedApproval>(`/workspaces/${workspaceId}/live-monitoring/auto-flow/saved-approval`)
      .then(v => { if (!cancelled) setGranted(Boolean(v.granted)); })
      .catch(() => { if (!cancelled) setError("Screen-sharing approval could not be loaded."); });
    return () => { cancelled = true; };
  }, [workspaceId, user?.id, mode]);

  const changeApproval = async (checked: boolean) => {
    if (!workspaceId || busy || granted === null) return;
    setBusy(true);
    setError("");
    try {
      const result = await api.request<SavedApproval>(
        `/workspaces/${workspaceId}/live-monitoring/auto-flow/saved-approval`,
        { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ granted: checked }) },
      );
      setGranted(Boolean(result.granted));
    } catch {
      setError("Unable to update approval. Please try again.");
    } finally {
      setBusy(false);
    }
  };

  if (!workspaceId || mode !== "workspace" || !user) return null;
  return (
    <div data-wfos-screen-approval="v17" style={{ marginTop: 12, paddingTop: 12, borderTop: "1px solid #e7e9ed" }}>
      <label style={{ display: "flex", alignItems: "center", gap: 10, cursor: busy ? "wait" : "pointer", fontWeight: 600, fontSize: 13 }}>
        <input
          type="checkbox"
          checked={granted === true}
          disabled={busy || granted === null}
          onChange={e => void changeApproval(e.target.checked)}
          aria-label="Automatically approve future live screen-sharing requests"
        />
        Automatically approve future screen-sharing requests
      </label>
      <p style={{ margin: "6px 0 0", fontSize: 12, lineHeight: 1.45, color: "#62718a" }}>
        Separate, optional screen-sharing consent. This approval is used only with a
        visible WorkforceOS Companion sharing indicator and Stop Sharing control.
        Turn this off any time to revoke saved approval and end associated sharing.
      </p>
      {error && <p role="alert" style={{ color: "#b42318", fontSize: 12 }}>{error}</p>}
    </div>
  );
}
