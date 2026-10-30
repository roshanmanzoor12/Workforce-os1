"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api/client";
import { useWorkspace } from "@/contexts/workspace-context";

interface Plan {
  code: string;
  name: string;
  device_limit: number | null;
  workspace_limit: number;
  retention_days: number | null;
  monthly_amount_minor: number | null;
  currency: string;
  checkout_enabled: boolean;
}
interface Renewal {
  trial_eligible: boolean;
  catalog: Plan[];
  status: { restricted: boolean; can_manage_billing: boolean; billing_exempt: boolean };
}

export default function WorkspaceBillingPage() {
  const { workspaceId, refreshWorkspaceAccess } = useWorkspace();
  const [data, setData] = useState<Renewal | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const load = useCallback(async () => {
    if (!workspaceId) return;
    setError("");
    try {
      const result = await api.get<Renewal>(`/billing/workspaces/${workspaceId}/renewal`);
      setData(result);
      if (!result.status.restricted) void refreshWorkspaceAccess();
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Unable to load workspace billing."); }
  }, [workspaceId, refreshWorkspaceAccess]);
  useEffect(() => { setData(null); void load(); }, [load]);

  async function checkout(plan: Plan, trial: boolean) {
    if (busy || !workspaceId) return;
    setBusy(true); setError("");
    try {
      const result = await api.post<{ url: string }>("/billing/checkout", {
        workspace_id: workspaceId, plan_code: plan.code, interval: "month", with_trial: trial,
      });
      const target = new URL(result.url);
      if (target.protocol !== "https:" || !["checkout.stripe.com", "billing.stripe.com", "invoice.stripe.com"].includes(target.hostname)) throw new Error("Invalid payment destination.");
      window.location.assign(target.href);
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Unable to open checkout."); setBusy(false); }
  }
  if (!workspaceId) return <main className="panel"><div className="panel-body">Select a workspace to manage its plan.</div></main>;
  return (
    <main className="workspace-renewal">
      <h1>Workspace billing</h1>
      <p>{data?.status.billing_exempt ? "Unlimited billing access is active. No trial or payment is required." : "Choose a plan for this workspace. Access resumes after the server verifies your payment."}</p>
      <p>This workspace uses its owner’s billing account. Payment covers the workspaces included in that account’s plan.</p>
      {error && <p role="alert">{error}</p>}
      <button type="button" disabled={busy} onClick={() => void load()}>Refresh payment status</button>
      {!data && !error && <p role="status">Loading workspace plans…</p>}
      {data && !data.status.restricted && <p role="status">Workspace access is active. You can return to your workspace.</p>}
      <div className="renewal-plans">
        {data?.catalog.map(plan => (
          <section key={plan.code}>
            <h2>{plan.name}</h2>
            <p>{plan.monthly_amount_minor === null ? "Price not configured" : new Intl.NumberFormat("en-US", { style: "currency", currency: plan.currency }).format(plan.monthly_amount_minor / 100) + " / month"}</p>
            <p>{plan.device_limit ?? "Unconfigured"} devices · {plan.workspace_limit} {plan.workspace_limit === 1 ? "workspace" : "workspaces"}</p>
            <p>{plan.retention_days ?? "Unconfigured"} days data retention</p>
            <button type="button" disabled={busy || !plan.checkout_enabled || plan.monthly_amount_minor === null || !data.status.restricted} onClick={() => void checkout(plan, false)}>{busy ? "Opening payment…" : "Choose plan"}</button>
            {data.trial_eligible && <button className="trial" type="button" disabled={busy || plan.device_limit === null || plan.retention_days === null} onClick={() => void checkout(plan, true)}>Start 3-day free trial</button>}
          </section>
        ))}
      </div>
      {data?.trial_eligible && <p>A card is required for the trial. No subscription charge today and no automatic charge when the trial ends. Your bank may display a temporary card verification hold.</p>}
      <style jsx>{`
        .workspace-renewal { background: #fffdf7; color: #10243a; padding: clamp(20px, 4vw, 40px); border: 1px solid #eadbb7; border-radius: 12px; }
        h1 { font-size: 28px; margin: 0 0 12px; } h2 { font-size: 22px; }
        p { max-width: 70ch; line-height: 1.6; } [role="alert"] { color: #a42518; }
        .renewal-plans { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; margin-block: 24px; }
        section { padding: 20px; border: 1px solid #eadbb7; border-radius: 12px; min-width: 0; }
        button { padding: 12px 16px; border: 1px solid #10243a; border-radius: 8px; background: #10243a; color: white; cursor: pointer; font: inherit; }
        section button { width: 100%; } .trial { margin-top: 12px; background: #ffdf36; color: #10243a; }
        button:disabled { opacity: .5; cursor: not-allowed; } button:focus-visible { outline: 3px solid #a66e00; outline-offset: 3px; }
        @media (max-width: 850px) { .renewal-plans { grid-template-columns: 1fr; } }
      `}</style>
    </main>
  );
}
