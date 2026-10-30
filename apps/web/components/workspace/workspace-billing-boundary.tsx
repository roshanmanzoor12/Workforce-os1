"use client";

import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import { usePathname } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api/client";
import { useWorkspace } from "@/contexts/workspace-context";

interface BillingStatus {
  workspace_id: string;
  plan_code: string;
  status: string;
  restricted: boolean;
  can_manage_billing: boolean;
  features: Record<string, boolean>;
}

const FEATURES: Record<string, string> = {
  "/payroll": "payroll", "/reports": "reports", "/meetings": "meetings",
  "/channels": "channels", "/monitoring": "monitoring",
  "/screen-monitoring": "live_screen", "/live-monitoring": "live_screen",
  "/employee-monitoring": "monitoring", "/analytics": "reports",
};

export function WorkspaceBillingBoundary({ children }: { children: ReactNode }) {
  const { workspaceId, mode, loading } = useWorkspace();
  const pathname = usePathname();
  const [snapshot, setSnapshot] = useState<BillingStatus | null>(null);
  const [failure, setFailure] = useState(false);
  const [retry, setRetry] = useState(0);
  const [dismissed, setDismissed] = useState<string | null>(null);
  const dialog = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    setSnapshot(null);
    setFailure(false);
    setDismissed(null);
    if (loading || mode !== "workspace" || !workspaceId) return;
    let stopped = false;
    let running = false;
    async function read() {
      if (running) return;
      running = true;
      try {
        const result = await api.get<BillingStatus>(`/billing/workspaces/${workspaceId}/status`);
        if (!stopped) { setSnapshot(result); setFailure(false); }
      } catch {
        if (!stopped) setFailure(true);
      } finally { running = false; }
    }
    const resume = () => { if (!document.hidden) void read(); };
    void read();
    const timer = window.setInterval(resume, 15000);
    window.addEventListener("focus", resume);
    document.addEventListener("visibilitychange", resume);
    return () => {
      stopped = true;
      window.clearInterval(timer);
      window.removeEventListener("focus", resume);
      document.removeEventListener("visibilitychange", resume);
    };
  }, [workspaceId, mode, loading, retry]);

  const current = snapshot?.workspace_id === workspaceId ? snapshot : null;
  const manager = current?.can_manage_billing === true;
  const billingRoute = pathname === "/billing" || pathname.startsWith("/billing/");
  const showReminder = current?.restricted && manager && dismissed !== workspaceId && !billingRoute;
  useEffect(() => {
    if (showReminder && !dialog.current?.open) dialog.current?.showModal();
    if (!showReminder && dialog.current?.open) dialog.current?.close();
  }, [showReminder]);
  const closeReminder = useCallback(() => {
    setDismissed(workspaceId);
    dialog.current?.close();
  }, [workspaceId]);

  if (mode !== "workspace") return <>{children}</>;
  const feature = Object.entries(FEATURES).find(([route]) => pathname === route || pathname.startsWith(`${route}/`))?.[1];
  // Managers can reach renewal while expired. No child workspace page is mounted
  // while checking, on failure, or after dismissing the renewal dialog.
  const allowed = !failure && current !== null && (
    (billingRoute && manager) || (!current.restricted && (!feature || current.features[feature] === true))
  );
  return (
    <>
      {allowed ? children : (
        <section className="panel" aria-live="polite">
          <div className="panel-body">
            <h2>{!failure && !current ? "Checking workspace access…" : manager ? "Choose or renew your workspace plan" : "Workspace unavailable"}</h2>
            <p>{failure ? "Workspace access could not be verified. Please retry." : manager ? "Workspace access is paused until a plan payment is confirmed." : "Workspace access is currently unavailable."}</p>
            {manager && <Link href="/billing/workspace">Choose or renew plan</Link>}
            {failure && <button type="button" onClick={() => setRetry(value => value + 1)}>Retry</button>}
          </div>
        </section>
      )}
      <dialog ref={dialog} aria-labelledby="workspace-renewal-title" onCancel={closeReminder}
        onClose={() => setDismissed(workspaceId)}
        style={{ border: "1px solid #eadbb7", borderRadius: 12, padding: 24, maxWidth: 460, width: "calc(100% - 32px)", background: "#fffdf7", color: "#10243a" }}>
        <h2 id="workspace-renewal-title">Choose or renew your workspace plan</h2>
        <p>Your trial or paid access has ended. Workspace access resumes after payment is confirmed.</p>
        <p>Closing this message keeps the workspace locked.</p>
        <Link href="/billing/workspace" onClick={closeReminder}>Open workspace billing</Link>
        <button type="button" onClick={closeReminder} style={{ marginInlineStart: 16 }}>Close</button>
      </dialog>
    </>
  );
}
