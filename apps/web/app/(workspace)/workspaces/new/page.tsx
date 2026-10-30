"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { ArrowLeft, ArrowRight, BriefcaseBusiness, Building2, Check, CheckCircle2, ChevronRight, Loader2, ShieldCheck } from "lucide-react";
import { api, ApiError } from "@/lib/api/client";
import { getAuthSession } from "@/lib/auth/session";
import { useWorkspace } from "@/contexts/workspace-context";
import { workspacesService } from "@/services/workspaces.service";
import { getWorkspaceTemplate } from "@/lib/workspace/templates";
import type { WorkspaceType, WorkspacePublic } from "@/types/workspace";

interface Access { allowed: boolean; reason: string | null; workspace_limit: number | null; workspace_count: number; }
interface Draft { name: string; type: WorkspaceType; timezone: string; slug: string; id: string | null; }
const zones = ["UTC", "Asia/Karachi", "Asia/Dubai", "Asia/Kolkata", "Europe/London", "America/New_York", "America/Chicago", "America/Los_Angeles", "Australia/Sydney"];
const key = (owner: string) => `workforce:workspace-setup:v1:${owner}`;
function readDraft(owner: string): Draft | null {
  try {
    const value: unknown = JSON.parse(sessionStorage.getItem(key(owner)) ?? "null");
    if (!value || typeof value !== "object") return null;
    const draft = value as Partial<Draft>;
    if (typeof draft.name !== "string" || draft.name.length > 200 ||
        !["company", "agency"].includes(draft.type ?? "") || typeof draft.timezone !== "string" ||
        typeof draft.slug !== "string" || !/^[a-z0-9-]{2,100}$/.test(draft.slug) ||
        (draft.id !== null && (typeof draft.id !== "string" || !/^[a-f0-9-]{36}$/i.test(draft.id)))) return null;
    return draft as Draft;
  } catch { return null; }
}
function saveDraft(owner: string, draft: Draft) { try { sessionStorage.setItem(key(owner), JSON.stringify(draft)); } catch { /* Server state remains authoritative. */ } }

export default function CreateWorkspacePage() {
  const { user, loading, openCreatedWorkspace, refreshBilling } = useWorkspace();
  const [step, setStep] = useState(1);
  const [type, setType] = useState<WorkspaceType | null>(null);
  const [name, setName] = useState("");
  const [timezone, setTimezone] = useState("UTC");
  const [access, setAccess] = useState<Access | null>(null);
  const [accessBusy, setAccessBusy] = useState(true);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [phase, setPhase] = useState("");
  const [created, setCreated] = useState<WorkspacePublic | null>(null);
  const [uncertain, setUncertain] = useState(false);
  const [retry, setRetry] = useState(0);
  const owner = user?.id;
  const draft = useRef<Draft | null>(null);
  const inFlight = useRef(false);
  const words = getWorkspaceTemplate(type);
  const title = useRef<HTMLHeadingElement>(null);

  useEffect(() => { title.current?.focus(); }, [step]);
  useEffect(() => {
    setAccess(null); setAccessBusy(true); setError(""); setCreated(null); setUncertain(false); draft.current = null;
    if (!owner || loading) return;
    const saved = readDraft(owner);
    if (saved) {
      draft.current = saved; setType(saved.type); setName(saved.name); setTimezone(saved.timezone); setStep(3); setUncertain(true);
    } else {
      setType(null); setName(""); setStep(1);
      setTimezone(Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC");
    }
    let stopped = false;
    api.get<Access>("/billing/workspace-access").then(result => { if (!stopped) setAccess(result); })
      .catch(cause => { if (!stopped) setError(cause instanceof Error ? cause.message : "Workspace eligibility could not be checked."); })
      .finally(() => { if (!stopped) setAccessBusy(false); });
    return () => { stopped = true; };
  }, [owner, loading, retry]);

  function currentOwner(id: string) { return getAuthSession()?.user?.id === id; }
  async function open(workspace: WorkspacePublic, id: string, provisioning = false) {
    if (!currentOwner(id)) return;
    setCreated(workspace); setUncertain(provisioning);
    if (workspace.status !== "ready") return;
    setPhase("Opening your workspace…");
    await refreshBilling();
    if (!currentOwner(id)) return;
    await openCreatedWorkspace(workspace.id);
    try { sessionStorage.removeItem(key(id)); } catch { /* No account data is required from storage. */ }
  }
  async function checkExisting() {
    if (!owner || inFlight.current || !draft.current) return;
    const id = owner; inFlight.current = true; setBusy(true); setError(""); setPhase("Checking workspace status…");
    try {
      const record = draft.current.id
        ? await workspacesService.get(draft.current.id)
        : (await workspacesService.list()).workspaces.find(item => item.workspace.slug === draft.current?.slug && item.workspace.created_by_user_id === id);
      const existing = record?.workspace;
      if (!currentOwner(id)) return;
      if (!existing) { setError("Creation has not been confirmed yet. Wait a moment, then check again before creating another workspace."); return; }
      draft.current = { ...draft.current, id: existing.id }; saveDraft(id, draft.current);
      await open(existing, id, record?.tenant?.status === "provisioning");
    } catch (cause) { if (currentOwner(id)) setError(cause instanceof Error ? cause.message : "Workspace status could not be checked."); }
    finally { inFlight.current = false; setBusy(false); setPhase(""); }
  }
  async function createOrProvision() {
    if (!owner || !type || inFlight.current || uncertain || (!created && !access?.allowed)) return;
    const id = owner; inFlight.current = true; setBusy(true); setError("");
    let workspaceId = created?.id ?? null;
    try {
      if (!workspaceId) {
        const normalized = name.trim().replace(/\s+/g, " ");
        if (normalized.length < 2 || normalized.length > 200) throw new Error("Enter a workspace name between 2 and 200 characters.");
        const slug = `${normalized.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 78).replace(/-$/, "") || "workspace"}-${crypto.randomUUID().replaceAll("-", "").slice(0, 10)}`;
        draft.current = { name: normalized, type, timezone, slug, id: null }; saveDraft(id, draft.current);
        setPhase("Creating your workspace…");
        const result = await workspacesService.create({ name: normalized, workspace_type: type, timezone, slug });
        if (!currentOwner(id)) return;
        workspaceId = result.workspace.id; setCreated(result.workspace);
        draft.current = { ...draft.current, id: workspaceId }; saveDraft(id, draft.current);
      }
      if (!currentOwner(id)) return;
      const detail = await workspacesService.get(workspaceId);
      const latest = detail.workspace;
      if (!currentOwner(id)) return;
      if (detail.tenant?.status === "provisioning") { await open(latest, id, true); return; }
      if (latest.status === "ready") { await open(latest, id); return; }
      if (["suspended", "archived"].includes(latest.status)) throw new Error("This workspace is not available for setup.");
      setPhase("Preparing your workspace…");
      if (latest.status === "failed") await workspacesService.retryProvisioning(workspaceId);
      else await workspacesService.provision(workspaceId);
      if (!currentOwner(id)) return;
      await open((await workspacesService.get(workspaceId)).workspace, id);
    } catch (cause) {
      if (!currentOwner(id)) return;
      const message = cause instanceof Error ? cause.message : "Workspace setup could not finish.";
      if (!workspaceId) {
        const definitive = cause instanceof ApiError && [400, 401, 402, 403, 409, 422].includes(cause.status);
        setUncertain(!definitive && draft.current !== null);
        if (definitive) { try { sessionStorage.removeItem(key(id)); } catch {} draft.current = null; }
      } else {
        // A provisioning failure must never issue another create request.
        setUncertain(true);
      }
      setError(message);
    } finally { inFlight.current = false; setBusy(false); setPhase(""); }
  }
  const preview = [words.profile, words.departments, words.teams, words.employees, words.members, words.clients, words.people, "Communication", words.work, words.finance, words.monitoring, words.ai, words.reports, "Administration"];
  const allZones = [...new Set([timezone, ...zones])];
  if (loading) return <main className="setup-loading" role="status">Loading your account…</main>;
  return <main className="setup">
    <Link className="back-home" href="/home"><ArrowLeft size={16} />Back to personal home</Link>
    <div className="setup-frame">
      <div className="setup-main">
        <ol className="steps" aria-label="Workspace setup progress">{["Workspace style", "Your details", "Review & create"].map((label, index) => <li key={label} aria-current={step === index + 1 ? "step" : undefined} className={step >= index + 1 ? "reached" : ""}><span>{step > index + 1 ? <Check size={14} /> : index + 1}</span>{label}</li>)}</ol>
        <h1 ref={title} tabIndex={-1}>{step === 1 ? "How does your team work?" : step === 2 ? `Make this ${words.title.toLowerCase()} workspace yours.` : created ? "Your workspace is being prepared." : "Ready to bring your team together?"}</h1>
        <p className="intro">{step === 1 ? "Choose a workspace style. We’ll organize the page names around the way you work." : step === 2 ? "Start with a name your team will recognize. Your timezone keeps workspace dates consistent." : "Review your choices. Your plan’s workspace allowance and features will apply."}</p>
        {step === 1 && <fieldset className="choices"><legend className="sr-only">Workspace style</legend>{(["company", "agency"] as const).map(kind => {
          const template = getWorkspaceTemplate(kind); const Icon = kind === "company" ? Building2 : BriefcaseBusiness;
          return <label key={kind} className={`choice ${type === kind ? "selected" : ""}`}><input type="radio" name="workspace-style" value={kind} checked={type === kind} onChange={() => setType(kind)} /><span className="choice-top"><span className="choice-icon"><Icon size={27} strokeWidth={1.7} /></span><span className="radio-mark">{type === kind && <Check size={13} />}</span></span><strong>{template.title}</strong><span className="choice-copy">{template.description}</span><span className="choice-list">{kind === "company" ? "Company · Departments · Employees" : "Agency · Delivery teams · Client projects"}</span></label>;
        })}</fieldset>}
        {step === 2 && <form id="workspace-details" onSubmit={event => { event.preventDefault(); if (name.trim().length >= 2) { setError(""); setStep(3); } }}>
          <label className="field">{words.title} workspace name<input required minLength={2} maxLength={200} value={name} onChange={event => setName(event.target.value)} placeholder={type === "agency" ? "e.g. Digital Promotix" : "e.g. Acme Company"} autoComplete="organization" /></label>
          <label className="field">Workspace timezone<select value={timezone} onChange={event => setTimezone(event.target.value)}>{allZones.map(zone => <option key={zone} value={zone}>{zone.replaceAll("_", " ")}</option>)}</select></label>
          <p className="hint">You can update the workspace name and timezone later in its settings.</p>
        </form>}
        {step === 3 && <><dl className="review"><div><dt>Workspace</dt><dd>{name.trim()}</dd></div><div><dt>Style</dt><dd>{words.title}</dd></div><div><dt>Timezone</dt><dd>{timezone.replaceAll("_", " ")}</dd></div><div><dt>Allowance</dt><dd>{accessBusy ? "Checking…" : access ? access.workspace_limit === null ? "Unlimited workspaces" : `${access.workspace_count} of ${access.workspace_limit} workspaces used` : "Could not verify"}</dd></div>{created && <div><dt>Setup status</dt><dd>{created.status}</dd></div>}</dl><p className="hint"><ShieldCheck size={17} />Your workspace is private. Invite your team after setup.</p></>}
        {error && <div className="message error" role="alert">{error}</div>}
        {!accessBusy && access && !access.allowed && !created && !uncertain && <div className="message" role="status">{access.reason || "Your current plan does not allow another workspace."} <Link href="/billing">View plans</Link></div>}
        {!accessBusy && !access && <button className="text-button" type="button" onClick={() => setRetry(value => value + 1)}>Retry eligibility check</button>}
        {(phase || busy) && <p className="progress" role="status"><Loader2 size={17} className="spin" />{phase || "Working…"}</p>}
        <div className="setup-actions">
          {step > 1 && !created && !uncertain && <button className="button secondary" type="button" disabled={busy} onClick={() => { setError(""); setStep(value => value - 1); }}><ArrowLeft size={16} />Back</button>}
          {step === 1 && <button className="button primary" type="button" disabled={!type} onClick={() => setStep(2)}>Continue<ArrowRight size={17} /></button>}
          {step === 2 && <button className="button primary" type="submit" form="workspace-details">Review workspace<ArrowRight size={17} /></button>}
          {step === 3 && uncertain && <button className="button primary" type="button" disabled={busy} onClick={() => void checkExisting()}>Check workspace status<ChevronRight size={17} /></button>}
          {step === 3 && !uncertain && <button className="button primary" type="button" disabled={busy || (!created && (accessBusy || !access?.allowed))} onClick={() => void createOrProvision()}>{busy ? "Setting up…" : created?.status === "ready" ? "Open workspace" : created ? "Finish workspace setup" : "Create workspace"}<ArrowRight size={17} /></button>}
        </div>
      </div>
      <aside className="setup-preview" aria-label="Workspace page preview"><div className="preview-brand"><span>{type === "agency" ? <BriefcaseBusiness size={21} /> : <Building2 size={21} />}</span><div><strong>{name.trim() || `Your ${words.title.toLowerCase()} workspace`}</strong><small>{words.title} style</small></div></div><div className="preview-home"><CheckCircle2 size={18} />{words.home}</div><p className="preview-label">Your workspace pages</p><ul>{preview.map(item => <li key={item}><span />{item}</li>)}</ul><p className="preview-note">Page names adapt to your style. Access follows your plan and each member’s permissions.</p></aside>
    </div>
    <style jsx>{`
      .setup { --setup-bg: var(--color-panel-background, #fffefa); --setup-ink: var(--color-text-primary, #1b2630); --setup-muted: var(--color-text-secondary, #606c78); --setup-line: var(--color-border, #e6dece); padding: clamp(18px, 4vw, 48px); color: var(--setup-ink); }
      :global(.setup .back-home) { display: inline-flex; gap: 8px; align-items: center; margin-bottom: 24px; font-size: 13px; color: var(--setup-muted); text-decoration: none; }
      .setup-frame { max-width: 1120px; margin: 0 auto; display: grid; grid-template-columns: minmax(0, 1fr) 300px; border-radius: 16px; background: var(--setup-bg); box-shadow: 0 14px 44px rgba(35, 31, 24, .08); overflow: hidden; }
      .setup-main { padding: clamp(22px, 4vw, 48px); min-width: 0; } h1 { font-size: clamp(26px, 3vw, 36px); letter-spacing: -.03em; line-height: 1.18; max-width: 21ch; margin: 36px 0 14px; outline: none; }
      .intro { margin: 0 0 30px; color: var(--setup-muted); line-height: 1.7; font-size: 14px; max-width: 60ch; }
      .steps { padding: 0; margin: 0; display: flex; flex-wrap: wrap; gap: 14px 20px; list-style: none; } .steps li { display: flex; align-items: center; gap: 7px; font-size: 11px; color: var(--setup-muted); } .steps li > span { display: grid; place-items: center; width: 23px; height: 23px; border: 1px solid var(--setup-line); border-radius: 50%; } .steps .reached > span { background: #ffda35; color: #242312; border-color: #ffda35; } .steps [aria-current="step"] { color: var(--setup-ink); font-weight: 700; }
      .choices { border: 0; padding: 0; margin: 0; display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
      .choice { position: relative; border: 1px solid var(--setup-line); border-radius: 12px; padding: 22px; display: flex; flex-direction: column; gap: 14px; cursor: pointer; } .choice.selected { border-color: #b18000; background: rgba(255, 213, 62, .1); } .choice:focus-within { outline: 3px solid #ad7900; outline-offset: 3px; } .choice input { position: absolute; opacity: 0; width: 1px; height: 1px; }
      .choice-top { display: flex; align-items: center; justify-content: space-between; } .choice-icon { display: grid; place-items: center; width: 52px; height: 52px; background: #ffe78c; color: #292a21; border-radius: 12px; } .radio-mark { display: grid; place-items: center; width: 19px; height: 19px; border: 1px solid #b8b09d; border-radius: 50%; } .selected .radio-mark { background: #292f33; border-color: #292f33; color: white; }
      .choice strong { font-size: 21px; } .choice-copy { color: var(--setup-muted); font-size: 13px; line-height: 1.65; } .choice-list { font-size: 11px; color: var(--setup-muted); line-height: 1.6; margin-top: auto; }
      .field { display: grid; gap: 9px; margin-bottom: 23px; font-size: 13px; font-weight: 600; } .field input, .field select { width: 100%; border: 1px solid var(--setup-line); border-radius: 8px; padding: 13px 14px; background: var(--setup-bg); color: var(--setup-ink); font: inherit; font-size: 16px; box-sizing: border-box; } .field input:focus-visible, .field select:focus-visible { outline: 2px solid #ad7900; outline-offset: 2px; }
      .hint { color: var(--setup-muted); font-size: 12px; line-height: 1.7; display: flex; gap: 8px; align-items: center; } .hint svg { flex: 0 0 auto; }
      .review { margin: 0 0 23px; border-block: 1px solid var(--setup-line); } .review > div { padding: 16px 0; display: grid; grid-template-columns: 110px minmax(0, 1fr); gap: 16px; border-bottom: 1px solid var(--setup-line); font-size: 13px; } .review > div:last-child { border: 0; } dt { color: var(--setup-muted); } dd { margin: 0; font-weight: 600; overflow-wrap: anywhere; }
      .setup-actions { display: flex; align-items: center; justify-content: flex-end; gap: 12px; margin-top: 32px; flex-wrap: wrap; } .button { display: inline-flex; align-items: center; justify-content: center; gap: 9px; padding: 12px 18px; border-radius: 8px; font: inherit; font-size: 13px; font-weight: 600; cursor: pointer; min-height: 44px; } .primary { border: 1px solid #292f33; background: #292f33; color: white; } .primary:hover { background: #40484d; } .secondary { background: transparent; border: 1px solid var(--setup-line); color: inherit; margin-inline-end: auto; } .button:focus-visible, .text-button:focus-visible { outline: 3px solid #ad7900; outline-offset: 3px; } .button:disabled { opacity: .5; cursor: not-allowed; }
      .message { padding: 14px; background: rgba(255, 213, 62, .14); border-radius: 8px; font-size: 13px; line-height: 1.7; margin-top: 22px; } .message.error { color: #b33827; background: rgba(230, 76, 50, .08); } .message a { color: inherit; font-weight: 700; } .text-button { padding: 8px 0; border: 0; background: transparent; color: inherit; text-decoration: underline; cursor: pointer; } .progress { display: flex; align-items: center; gap: 8px; font-size: 13px; }
      .setup-preview { padding: 28px 22px; border-inline-start: 1px solid var(--setup-line); background: rgba(232, 219, 185, .08); } .preview-brand { display: flex; align-items: center; gap: 10px; padding-bottom: 22px; } .preview-brand > span { display: grid; place-items: center; width: 43px; height: 43px; border-radius: 9px; color: #242719; background: #ffdc54; flex-shrink: 0; } .preview-brand strong { display: block; font-size: 13px; line-height: 1.5; overflow-wrap: anywhere; } .preview-brand small { color: var(--setup-muted); font-size: 11px; }
      .preview-home { display: flex; align-items: center; gap: 10px; padding: 13px; color: white; background: #292f33; border-radius: 8px; font-size: 13px; font-weight: 600; } .preview-label { margin: 24px 0 12px; font-size: 12px; color: var(--setup-muted); } .setup-preview ul { margin: 0; padding: 0; list-style: none; } .setup-preview li { display: flex; align-items: center; gap: 10px; padding: 8px 5px; font-size: 12px; } .setup-preview li span { width: 5px; height: 5px; background: #c69a2b; border-radius: 50%; } .preview-note { border-top: 1px solid var(--setup-line); padding-top: 18px; margin-top: 20px; color: var(--setup-muted); font-size: 11px; line-height: 1.7; }
      .sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0,0,0,0); white-space: nowrap; border: 0; } .spin { animation: spin 1s linear infinite; } @keyframes spin { to { transform: rotate(360deg); } } @media (prefers-reduced-motion: reduce) { .spin { animation: none; } }
      @media (max-width: 1050px) { .setup-frame { grid-template-columns: minmax(0, 1fr); } .setup-preview { border-inline-start: 0; border-top: 1px solid var(--setup-line); } .setup-preview ul { display: grid; grid-template-columns: 1fr 1fr; } }
      @media (max-width: 560px) { .choices { grid-template-columns: 1fr; } .setup { padding: 16px; } .setup-main { padding: 24px 18px; } h1 { font-size: 28px; margin-top: 28px; } .steps { gap: 12px; } .steps li { font-size: 10px; } .choice-copy { font-size: 14px; } .button { width: 100%; font-size: 14px; } .intro { font-size: 15px; } }
    `}</style>
  </main>;
}
