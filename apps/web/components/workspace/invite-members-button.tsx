"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";
import { Check, Copy, UserPlus, X } from "lucide-react";
import { useWorkspace } from "@/contexts/workspace-context";
import { workspaceInvitationsService } from "@/services/workspace-invitations.service";
import { workspaceRolesService } from "@/services/workspace-roles.service";
import type { WorkspaceRolePublic } from "@/types/workspace-roles";
import type { WorkspaceInvitationSecretResponse } from "@/types/workspace-invitations";
import { buildWorkspaceInvitationLink } from "@/lib/workspace/invitation-link";

type Method = "calling" | "email" | "username" | "account";

export function InviteMembersButton() {
  const { workspaceId, permissions, isOwner } = useWorkspace();
  const permitted = isOwner || permissions.includes("*") || permissions.includes("members.invite");
  if (!workspaceId || !permitted) return null;
  return <InviteControl key={workspaceId} workspaceId={workspaceId} />;
}

function InviteControl({ workspaceId }: { workspaceId: string }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  const [method, setMethod] = useState<Method>("calling");
  const [identifier, setIdentifier] = useState("");
  const [roles, setRoles] = useState<WorkspaceRolePublic[]>([]);
  const [roleKey, setRoleKey] = useState("member");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<WorkspaceInvitationSecretResponse | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    let alive = true;
    workspaceRolesService.list(workspaceId)
      .then(data => { if (alive) setRoles(data.roles.filter(role => role.is_active && role.role_key !== "owner")); })
      .catch(() => { if (alive) setRoles([]); });
    return () => { alive = false; };
  }, [workspaceId]);

  function open() { setMethod("calling"); setIdentifier(""); setRoleKey("member"); setResult(null); setError(""); setCopied(false); dialog.current?.showModal(); }
  function close() { if (busy) return; dialog.current?.close(); trigger.current?.focus(); }
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy || !identifier.trim()) return;
    setBusy(true); setError("");
    try {
      const payload = method === "email"
        ? { email: identifier.trim(), role_key: roleKey }
        : { identifier: identifier.trim(), role_key: roleKey };
      setResult(await workspaceInvitationsService.create(workspaceId, payload));
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Could not send the invitation."); }
    finally { setBusy(false); }
  }
  const inviteUrl = result ? buildWorkspaceInvitationLink(result.invitation_token) : "";
  async function copy() {
    try { await navigator.clipboard.writeText(inviteUrl); setCopied(true); }
    catch { setError("Copy failed. Select the link and copy it manually."); }
  }

  return <>
    <button ref={trigger} type="button" className="wh-button wh-button-dark" onClick={open}><UserPlus size={16} /> Invite members</button>
    <dialog ref={dialog} aria-labelledby="workspace-invite-title" onCancel={e => { e.preventDefault(); close(); }} style={{ width: "min(500px, calc(100vw - 24px))", maxHeight: "90dvh", overflowY: "auto", margin: "auto", padding: 0, background: "#fffefa", color: "#252627", border: "1px solid #e4ded3", borderRadius: 14, boxShadow: "0 18px 70px #0003" }}>
      <header style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 12, padding: 24, borderBottom: "1px solid #ece7de" }}>
        <div><h2 id="workspace-invite-title" style={{ fontSize: 21 }}>Invite members</h2><p style={{ color: "#73777d", fontSize: 13, marginTop: 7 }}>Invite an account and assign workspace access.</p></div>
        <button type="button" className="button button--outline" aria-label="Close" onClick={close} disabled={busy}><X size={17} /></button>
      </header>
      {result ? <div style={{ padding: 24, display: "grid", gap: 13 }}>
        <Check size={25} color="#21865f" />
        <h3>Invitation created</h3>
        <p style={{ color: "#61656a", fontSize: 13 }}>Invitation for <strong>{result.invitation.email}</strong> as <strong>{result.invitation.role_key}</strong>.</p>
        <label htmlFor="workforce-invitation-link" style={{ fontWeight: 600, fontSize: 13 }}>Shareable invitation link</label>
        <textarea id="workforce-invitation-link" rows={3} readOnly value={inviteUrl} style={{ width: "100%", padding: 12, border: "1px solid #ddd", borderRadius: 8, resize: "vertical", overflowWrap: "anywhere" }} />
        <small>Only the invited account can accept this invitation. Keep the link private.</small>
        <div style={{ display: "flex", gap: 10 }}><button className="button button--outline" onClick={() => void copy()}><Copy size={15} /> {copied ? "Copied" : "Copy link"}</button><button className="button button--primary" onClick={close}>Done</button></div>
      </div> : <form onSubmit={e => void submit(e)} style={{ padding: 24, display: "grid", gap: 16 }}>
        <label className="field"><span className="field-label">Invite using</span><select className="select" value={method} onChange={e => { setMethod(e.target.value as Method); setIdentifier(""); }} disabled={busy}><option value="calling">Calling Number</option><option value="email">Email</option><option value="username">Username</option><option value="account">User ID</option></select></label>
        <label className="field"><span className="field-label">{method === "email" ? "Email address" : method === "calling" ? "Calling Number" : method === "username" ? "Username" : "Account User ID"}</span><input className="input" type={method === "email" ? "email" : "text"} required maxLength={method === "calling" ? 10 : 320} minLength={method === "calling" ? 10 : 3} inputMode={method === "calling" ? "numeric" : undefined} pattern={method === "calling" ? "[0-9]{10}" : undefined} placeholder={method === "email" ? "name@company.com" : method === "calling" ? "10-digit Calling Number" : method === "username" ? "@username" : "User ID"} value={identifier} onChange={e => setIdentifier(e.target.value)} disabled={busy} /></label>
        <label className="field"><span className="field-label">Workspace role</span><select className="select" value={roleKey} onChange={e => setRoleKey(e.target.value)} disabled={busy}>{(roles.length ? roles : [{ role_key: "member", display_name: "Member" }]).map(role => <option key={role.role_key} value={role.role_key}>{role.display_name}</option>)}</select></label>
        <p style={{ fontSize: 12, color: "#696b6e" }}>The selected role controls workspace access. Workspace Owners cannot be invited.</p>
        {error && <p role="alert" style={{ color: "#bd342e", fontSize: 13 }}>{error}</p>}
        <div style={{ display: "flex", justifyContent: "flex-end", gap: 10, borderTop: "1px solid #eee", paddingTop: 18 }}><button className="button button--outline" type="button" onClick={close}>Cancel</button><button className="button button--primary" type="submit" disabled={busy || !identifier.trim()}><UserPlus size={15} />{busy ? "Creating..." : "Create invitation"}</button></div>
      </form>}
      {result && error && <p role="alert" style={{ color: "#bd342e", padding: "0 24px 18px" }}>{error}</p>}
    </dialog>
    <style jsx global>{`dialog[aria-labelledby="workspace-invite-title"]::backdrop { background: rgba(25, 28, 31, 0.55); }`}</style>
  </>;
}
