"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState, type FormEvent, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { Bell, Building2, CreditCard, Laptop, ShieldCheck, UserRound, Link2, RefreshCcw } from "lucide-react";
import { useWorkspace } from "@/contexts/workspace-context";
import { api } from "@/lib/api/client";
import { CallingNumber } from "@/components/account/calling-number";
import { ProfilePhotoPicker } from "@/components/account/profile-photo-picker";
import { authService } from "@/services/auth.service";
import { billingService } from "@/services/billing.service";
import { workspacesService } from "@/services/workspaces.service";
import { personalAccountService, type PersonalAccount } from "@/services/personal-account.service";
import type { AuthSessionItem } from "@/types/auth";
import type { BillingPlanPublic } from "@/types/billing";

export type SettingsSection = "account" | "workspace" | "security" | "notifications" | "integrations" | "billing" | "devices" | "activity";
const tabs: { id: SettingsSection; title: string; icon: typeof UserRound }[] = [
  { id: "account", title: "Profile", icon: UserRound },
  { id: "security", title: "Security", icon: ShieldCheck },
  { id: "devices", title: "Devices", icon: Laptop },
  { id: "activity", title: "Account activity", icon: RefreshCcw },
  { id: "notifications", title: "Notifications", icon: Bell },
  { id: "integrations", title: "Connected accounts", icon: Link2 },
  { id: "workspace", title: "Workspaces", icon: Building2 },
  { id: "billing", title: "Billing", icon: CreditCard },
];

function date(value: string | null | undefined) {
  if (!value) return "Not recorded";
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? "Not recorded" : parsed.toLocaleString();
}
function message(error: unknown): string {
  return error instanceof Error ? error.message : "The request failed. Please retry.";
}
export function AccountCard({ title, children }: { title: string; children: ReactNode }) {
  return <section className="pa-card"><h2>{title}</h2>{children}</section>;
}
function Field({ label, children }: { label: string; children: ReactNode }) {
  return <label className="pa-field"><span>{label}</span>{children}</label>;
}

export function PersonalSettingsClient({ section = "account", profile = false }: { section?: SettingsSection; profile?: boolean }) {
  const { user, loading, error: accountError, refreshBootstrap, workspaces } = useWorkspace();
  if (loading && !user) return <p role="status">Loading your account...</p>;
  if (!user) return <div className="pa-page"><h1>Personal account</h1><p role="alert">{accountError || "Sign in to manage your account."}</p><Link href="/login">Sign in</Link></div>;
  const name = [user.first_name, user.last_name].filter(Boolean).join(" ") || user.username;
  return <div className="pa-page">
    <header className="pa-header"><div><h1>{profile ? "Personal profile" : "Account settings"}</h1><p>Your identity, security and preferences across WorkforceOS.</p></div><Link className="button button--outline" href="/home">Back to dashboard</Link></header>
    {accountError ? <div className="pa-notice" role="alert">{accountError}<button className="button" onClick={() => void refreshBootstrap()}>Retry account</button></div> : null}
    <div className="pa-profileHero"><ProfilePhotoPicker /><div><h2>{name}</h2><p>{user.email}</p><span className="pa-badge">{user.is_email_verified ? "Verified email" : "Verification pending"}</span></div><div className="pa-heroMeta"><strong>{workspaces.filter(item => item.membership.status === "active").length}</strong><span>Joined workspaces</span></div></div>
    <nav className="pa-tabs" aria-label="Personal account settings">{tabs.map(tab => <Link key={tab.id} href={`/settings/${tab.id}`} aria-current={section === tab.id ? "page" : undefined}><tab.icon size={16} aria-hidden="true" />{tab.title}</Link>)}</nav>
    {section === "account" ? <ProfileForm /> : null}
    {section === "security" || section === "devices" || section === "activity" || section === "integrations" ? <SecurityPanel section={section} /> : null}
    {section === "workspace" ? <WorkspacePanel /> : null}
    {section === "notifications" ? <NotificationsPanel /> : null}
    {section === "billing" ? <BillingPanel /> : null}
  </div>;
}

function ProfileForm() {
  const { user, updateUser } = useWorkspace();
  const [form, setForm] = useState({ username: user?.username || "", first_name: user?.first_name || "", last_name: user?.last_name || "", avatar_url: user?.avatar_url || "" });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  // Keying on identity protects one account's draft from a later signed-in user.
  useEffect(() => {
    setForm({ username: user?.username || "", first_name: user?.first_name || "", last_name: user?.last_name || "", avatar_url: user?.avatar_url || "" });
    setSaved(false); setError(null);
  }, [user?.id]); // Updates to the same account do not overwrite an unsaved draft.
  async function save(event: FormEvent) {
    event.preventDefault(); setBusy(true); setSaved(false); setError(null);
    try {
      const response = await personalAccountService.update({ username: form.username.trim(), first_name: form.first_name.trim() || null, last_name: form.last_name.trim() || null });
      updateUser(response.user);
      setForm({ username: response.user.username, first_name: response.user.first_name || "", last_name: response.user.last_name || "", avatar_url: response.user.avatar_url || "" });
      setSaved(true);
    } catch (cause) { setError(message(cause)); } finally { setBusy(false); }
  }
  function input(key: keyof typeof form, label: string, maximum: number, type = "text") {
    return <Field label={label}><input type={type} maxLength={maximum} required={key === "username"} minLength={key === "username" ? 3 : undefined} autoComplete={key === "first_name" ? "given-name" : key === "last_name" ? "family-name" : key === "username" ? "username" : "off"} value={form[key]} disabled={busy} onChange={event => { setSaved(false); setForm(current => ({ ...current, [key]: event.target.value })); }} /></Field>;
  }
  return <div className="pa-twoColumns"><AccountCard title="Profile information"><form onSubmit={event => void save(event)}>
    <p className="pa-muted">These details belong to your personal account. Company roles and employee records are managed within each workspace.</p>
    <div className="pa-formGrid">{input("first_name", "First name", 100)}{input("last_name", "Last name", 100)}{input("username", "Username", 64)}<Field label="Email address"><input value={user?.email || ""} readOnly type="email" /><small>Your verified sign-in address.</small></Field></div>
    <p className="pa-muted">Click your profile photo above to upload a photo, use your Google photo, or choose a 3D avatar.</p>
    {error ? <p role="alert" className="pa-notice">{error}</p> : null}{saved ? <p role="status" className="pa-success">Profile saved to your account.</p> : null}
    <button className="button button--primary" disabled={busy} type="submit">{busy ? "Saving..." : "Save profile"}</button>
  </form></AccountCard><AccountCard title="Account details"><dl className="pa-details"><div><dt>Account ID</dt><dd><code>{user?.id}</code></dd></div><div><dt>Calling number</dt><dd><CallingNumber /></dd></div><div><dt>Status</dt><dd>{user?.is_locked ? "Locked" : user?.is_active ? "Active" : "Inactive"}</dd></div><div><dt>Joined</dt><dd>{date(user?.created_at)}</dd></div><div><dt>Updated</dt><dd>{date(user?.updated_at)}</dd></div></dl><Link href="/settings/security">Review your security</Link></AccountCard></div>;
}

function SecurityPanel({ section }: { section: SettingsSection }) {
  const { user } = useWorkspace();
  const router = useRouter();
  const [account, setAccount] = useState<PersonalAccount | null>(null);
  const [sessions, setSessions] = useState<AuthSessionItem[] | null>(null);
  const [errors, setErrors] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [action, setAction] = useState<string | null>(null);
  const generation = useRef(0);
  const load = useCallback(async () => {
    const request = ++generation.current; setBusy(true); setErrors([]);
    const results = await Promise.allSettled([personalAccountService.get(), authService.getSessions()]);
    if (request !== generation.current) return;
    const problems: string[] = [];
    if (results[0].status === "fulfilled") setAccount(results[0].value); else { setAccount(null); problems.push("Security details could not be loaded. Retry below."); }
    if (results[1].status === "fulfilled") setSessions(results[1].value.sessions); else { setSessions(null); problems.push("Session list could not be loaded. Retry below."); }
    setErrors(problems); setBusy(false);
  }, [user?.id]);
  useEffect(() => { setAccount(null); setSessions(null); void load(); return () => { generation.current++; }; }, [load]);
  async function revoke(id: string) {
    setAction(id); setErrors([]);
    try { await authService.revokeSession(id); await load(); } catch (cause) { setErrors([message(cause)]); } finally { setAction(null); }
  }
  async function logoutAll() {
    setAction("all");
    try { await authService.logoutAll(); router.replace("/login"); }
    catch (cause) { setErrors([message(cause)]); router.replace("/login"); }
  }
  const active = sessions?.filter(item => !item.revoked_at && new Date(item.expires_at).getTime() > Date.now()) || [];
  const list = section === "activity" ? sessions || [] : active;
  return <div className="pa-stack">
    <div className="pa-actions"><button className="button button--outline" disabled={busy || action !== null} onClick={() => void load()}>{busy ? "Loading..." : "Refresh security details"}</button></div>
    {errors.map(error => <p role="alert" className="pa-notice" key={error}>{error}</p>)}
    {section === "security" ? <div className="pa-twoColumns"><AccountCard title="Sign-in protection"><dl className="pa-details"><div><dt>Email verification</dt><dd>{user?.is_email_verified ? "Verified" : "Pending"}</dd></div><div><dt>Password</dt><dd>{account ? account.has_password ? "Password configured" : "Provider sign-in" : "Loading..."}</dd></div><div><dt>Last password change</dt><dd>{account ? date(account.password_changed_at) : "Loading..."}</dd></div><div><dt>Last sign-in</dt><dd>{account ? date(account.last_login_at) : "Loading..."}</dd></div></dl><Link className="button button--outline" href="/forgot-password">Reset password with email OTP</Link><p className="pa-muted">Two-factor authentication setup is not available in the current authentication backend.</p></AccountCard><AccountCard title="Session control"><strong className="pa-bigNumber">{sessions === null ? "—" : active.length}</strong><p>Active sessions</p><p className="pa-muted">Signing out everywhere includes this browser. Save your work first.</p><button className="button button--outline" disabled={action !== null || busy || sessions === null} onClick={() => void logoutAll()}>Sign out everywhere</button></AccountCard></div> : null}
    {section === "integrations" ? <AccountCard title="Connected sign-in accounts">{account ? account.identities.length ? <ul className="pa-list">{account.identities.map(identity => <li key={identity.provider}><div><strong>{identity.provider}</strong><small>{identity.email || "Email not provided"}</small><small>Connected {date(identity.connected_at)}</small></div><span className="pa-badge">Connected</span></li>)}</ul> : <p>No external sign-in accounts are connected.</p> : <p role="status">{busy ? "Loading connected accounts..." : "Connected accounts unavailable. Retry above."}</p>}<p className="pa-muted">Workspace apps such as Slack, Teams and payroll integrations are managed by the workspace. Provider linking and unlinking are not supported by the current API.</p></AccountCard> : <AccountCard title={section === "activity" ? "Session activity" : "Active sessions & devices"}>
      <p className="pa-muted">{section === "activity" ? "Sessions returned by your authentication service. This is not a complete audit history." : "Browser and device names come from your sign-in sessions."}</p>
      {sessions === null ? <p role="status">{busy ? "Loading sessions..." : "Sessions unavailable. Retry above."}</p> : list.length ? <ul className="pa-list">{list.map(session => {
        const isActive = !session.revoked_at && new Date(session.expires_at).getTime() > Date.now();
        return <li key={session.id}><div><strong>{session.device_name || "Browser session"}</strong><small>{session.user_agent || "Browser details not recorded"}</small><small>IP: {session.ip_address || "Not recorded"} · Last used: {date(session.last_used_at || session.created_at)}</small><small>Expires: {date(session.expires_at)} · {session.revoked_at ? "Revoked" : isActive ? "Active" : "Expired"}</small></div>{isActive ? <button className="button button--outline" disabled={action !== null || busy} onClick={() => void revoke(session.id)}>{action === session.id ? "Revoking..." : "Revoke session"}</button> : null}</li>;
      })}</ul> : <p>No sessions to display.</p>}
      <p className="pa-muted">Revoking the session used by this browser may require you to sign in again.</p>
    </AccountCard>}
  </div>;
}

function WorkspacePanel() {
  const { workspaces, switchWorkspace, refreshWorkspaces } = useWorkspace();
  const [selected, setSelected] = useState("");
  const [name, setName] = useState("");
  const [timezone, setTimezone] = useState("");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const active = workspaces.filter(item => item.membership.status === "active");
  const item = active.find(item => item.workspace.id === selected);
  const canEdit = item?.membership.role_key === "owner" || item?.membership.role_key === "admin";
  useEffect(() => { setName(item?.workspace.name || ""); setTimezone(item?.workspace.timezone || ""); setNotice(null); }, [selected, item?.workspace.updated_at]);
  async function save(event: FormEvent) {
    event.preventDefault(); if (!item || !canEdit) return;
    setBusy(true); setNotice(null);
    try { await workspacesService.update(item.workspace.id, { name: name.trim(), timezone: timezone.trim() }); await refreshWorkspaces(); setNotice("Workspace saved."); }
    catch (cause) { setNotice(message(cause)); } finally { setBusy(false); }
  }
  return <AccountCard title="Your workspace memberships"><p className="pa-muted">Your personal profile is shared across companies. Workspace details and your role belong to each company.</p>
    {active.length ? <><Field label="Workspace"><select disabled={busy} value={selected} onChange={event => setSelected(event.target.value)}><option value="">Choose a workspace</option>{active.map(item => <option key={item.workspace.id} value={item.workspace.id}>{item.workspace.name}</option>)}</select></Field>{item ? <><dl className="pa-details"><div><dt>Your role</dt><dd>{item.membership.role_key}</dd></div><div><dt>Workspace status</dt><dd>{item.workspace.status}</dd></div></dl><form onSubmit={event => void save(event)}><div className="pa-formGrid"><Field label="Workspace name"><input required maxLength={200} disabled={!canEdit || busy} value={name} onChange={event => setName(event.target.value)} /></Field><Field label="Timezone (IANA)"><input required disabled={!canEdit || busy} placeholder="Asia/Karachi" value={timezone} onChange={event => setTimezone(event.target.value)} /></Field></div>{canEdit ? <button type="submit" className="button button--primary" disabled={busy}>{busy ? "Saving..." : "Save workspace"}</button> : <p className="pa-muted">Workspace owners and administrators can update these details.</p>}</form><button className="button button--outline" disabled={busy || !item.workspace.is_active || item.workspace.status !== "ready"} onClick={() => switchWorkspace(item.workspace.id)}>Open workspace</button></> : null}</> : <p>You have no active workspace memberships.</p>}
    {notice ? <p role="status" className="pa-notice">{notice}</p> : null}
  </AccountCard>;
}

type NotificationPreferences = { in_app_enabled: boolean; email_enabled: boolean; push_enabled: boolean; sound_enabled: boolean; digest_enabled: boolean; digest_hour: number; muted_types: string[] };
function NotificationsPanel() {
  const { workspaces } = useWorkspace();
  const [selected, setSelected] = useState("");
  const [prefs, setPrefs] = useState<NotificationPreferences | null>(null);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const generation = useRef(0);
  const active = workspaces.filter(item => item.membership.status === "active" && item.workspace.is_active && item.workspace.status === "ready");
  const valid = active.some(item => item.workspace.id === selected);
  const path = `/workspaces/${encodeURIComponent(selected)}/notifications/preferences`;
  const load = useCallback(async () => {
    const request = ++generation.current; setPrefs(null); setNotice(null);
    if (!selected || !valid) { setBusy(false); return; }
    setBusy(true);
    try { const response = await api.get<NotificationPreferences>(path); if (generation.current === request) setPrefs(response); }
    catch (cause) { if (generation.current === request) setNotice(message(cause)); }
    finally { if (generation.current === request) setBusy(false); }
  }, [path, selected, valid]);
  useEffect(() => { void load(); return () => { generation.current++; }; }, [load]);
  async function save(event: FormEvent) {
    event.preventDefault(); if (!prefs || !valid) return;
    setBusy(true); setNotice(null);
    try { const response = await api.patch<NotificationPreferences>(path, prefs); setPrefs(response); setNotice("Workspace notification preferences saved."); }
    catch (cause) { setNotice(message(cause)); } finally { setBusy(false); }
  }
  return <AccountCard title="Notification preferences"><p className="pa-muted">Notification preferences currently belong to a workspace. Verification and password reset emails remain part of account security.</p><Field label="Workspace"><select value={selected} disabled={busy} onChange={event => setSelected(event.target.value)}><option value="">Choose a workspace</option>{active.map(item => <option value={item.workspace.id} key={item.workspace.id}>{item.workspace.name}</option>)}</select></Field>
    {!active.length ? <p>No ready workspace is available. Global personal notification preferences are not supported by the current API.</p> : null}
    {busy && !prefs ? <p role="status">Loading preferences...</p> : null}
    {notice ? <p role="status" className="pa-notice">{notice}</p> : null}
    {selected && valid && !prefs && !busy ? <button className="button" onClick={() => void load()}>Retry preferences</button> : null}
    {prefs ? <form onSubmit={event => void save(event)}>{([ ["in_app_enabled", "In-app notifications"], ["email_enabled", "Email notifications"], ["push_enabled", "Push notifications"], ["sound_enabled", "Notification sounds"], ["digest_enabled", "Daily digest"] ] as const).map(([key, title]) => <label className="pa-toggle" key={key}><span>{title}</span><input type="checkbox" disabled={busy} checked={prefs[key]} onChange={event => { setNotice(null); setPrefs({ ...prefs, [key]: event.target.checked }); }} /></label>)}<Field label="Digest hour (0–23)"><input type="number" min={0} max={23} required disabled={busy || !prefs.digest_enabled} value={prefs.digest_hour} onChange={event => setPrefs({ ...prefs, digest_hour: Number(event.target.value) })} /></Field><button className="button button--primary" disabled={busy}>{busy ? "Saving..." : "Save preferences"}</button><p className="pa-muted">These controls save the existing notification-service preferences. Email, push and digest delivery also require their backend delivery workers.</p></form> : null}
  </AccountCard>;
}

function BillingPanel() {
  const { user, subscription, workspaceAccess, refreshBootstrap, loading } = useWorkspace();
  const [plans, setPlans] = useState<BillingPlanPublic[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const generation = useRef(0);
  const load = useCallback(async () => {
    const request = ++generation.current; setBusy(true); setError(null);
    try { const response = await billingService.getPlans(); if (request === generation.current) setPlans(response.plans); }
    catch (cause) { if (request === generation.current) setError(message(cause)); }
    finally { if (request === generation.current) setBusy(false); }
  }, [user?.id]);
  useEffect(() => { setPlans(null); void load(); return () => { generation.current++; }; }, [load]);
  return <div className="pa-stack"><div className="pa-twoColumns"><AccountCard title="Your subscription">{subscription ? <><strong className="pa-planName">{plans?.find(plan => plan.code === subscription.plan_code)?.display_name || subscription.plan_code}</strong><dl className="pa-details"><div><dt>Status</dt><dd>{subscription.status}</dd></div><div><dt>Current period starts</dt><dd>{date(subscription.current_period_start)}</dd></div><div><dt>Current period ends</dt><dd>{date(subscription.current_period_end)}</dd></div></dl></> : <p>{loading ? "Loading subscription..." : "Subscription details unavailable."}</p>}<button className="button button--outline" disabled={loading} onClick={() => void refreshBootstrap()}>Refresh subscription</button></AccountCard><AccountCard title="Workspace access">{workspaceAccess ? <><p>{workspaceAccess.allowed ? "Workspace creation is available." : workspaceAccess.reason || "Workspace creation is unavailable on your current plan."}</p><dl className="pa-details"><div><dt>Owned workspaces</dt><dd>{workspaceAccess.workspace_count}</dd></div><div><dt>Workspace limit</dt><dd>{workspaceAccess.workspace_limit}</dd></div></dl>{workspaceAccess.allowed ? <Link className="button button--primary" href="/workspaces/new">Create workspace</Link> : null}</> : <p>Workspace access details unavailable. Refresh subscription.</p>}</AccountCard></div>
    <AccountCard title="Plan capabilities">{error ? <p role="alert" className="pa-notice">{error}</p> : null}<button className="button button--outline" disabled={busy} onClick={() => void load()}>{busy ? "Loading plans..." : "Refresh plans"}</button>{plans ? <div className="pa-tableWrap"><table className="pa-table"><thead><tr><th>Plan</th><th>Workspaces</th><th>Members per workspace</th><th>Monitoring</th></tr></thead><tbody>{plans.map(plan => <tr key={plan.code}><td>{plan.display_name}{subscription?.plan_code === plan.code ? " · Current" : ""}</td><td>{plan.workspace_limit}</td><td>{plan.member_limit_per_workspace}</td><td>{plan.monitoring_enabled ? "Included" : "Unavailable"}</td></tr>)}</tbody></table></div> : null}<p className="pa-muted">The current billing API provides plans and subscription access. Checkout, payment methods and invoice downloads are not exposed yet.</p></AccountCard>
  </div>;
}