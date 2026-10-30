"use client";

import { UserAvatar } from "@/components/account/user-avatar";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { MessageCircle, RefreshCcw, Search, UserPlus, Users } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { useWorkspace } from "@/contexts/workspace-context";
import { personalSocialService as service, type FriendAction, type PersonalFriend, type Person } from "@/services/personal-social.service";
import { workspaceInvitationsService } from "@/services/workspace-invitations.service";
import type { WorkspaceInvitationPublic } from "@/types/workspace-invitations";
import { socialChatService } from "@/services/social-chat.service";

type View = "friends" | "incoming" | "outgoing" | "blocked" | "invitations";
const tabs: [View, string][] = [["friends", "All friends"], ["incoming", "Requests"], ["outgoing", "Sent requests"], ["blocked", "Blocked"], ["invitations", "Invitations"]];
const reason = (error: unknown) => error instanceof Error ? error.message : "The request failed. Please try again.";

export default function FriendsPage() {
  const { user, loading: accountLoading, refreshWorkspaces, openCreatedWorkspace } = useWorkspace();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [items, setItems] = useState<PersonalFriend[]>([]);
  const [workspaceInvitations, setWorkspaceInvitations] = useState<WorkspaceInvitationPublic[]>([]);
  const [view, setView] = useState<View>(() => searchParams.get("tab") === "invitations" ? "invitations" : "friends");
  const [search, setSearch] = useState("");
  const [identifier, setIdentifier] = useState("");
  const [found, setFound] = useState<Person | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const lock = useRef(false);
  const generation = useRef(0);
  const lookupGeneration = useRef(0);
  const activeUser = useRef(user?.id);
  activeUser.current = user?.id;

  const load = useCallback(async () => {
    if (!user?.is_email_verified) return;
    const owner = user.id;
    const version = ++generation.current;
    try {
      const [response, invitationsResponse] = await Promise.all([service.friends(), workspaceInvitationsService.incoming()]);
      if (activeUser.current === owner && version === generation.current) {
        setItems(response.items); setWorkspaceInvitations(invitationsResponse.items); setError("");
      }
    } catch (cause) {
      if (activeUser.current === owner && version === generation.current) setError(reason(cause));
    } finally {
      if (activeUser.current === owner && version === generation.current) setLoading(false);
    }
  }, [user?.id, user?.is_email_verified]);

  useEffect(() => {
    setItems([]); setFound(null); setLoading(true);
    void load();
    const timer = window.setInterval(() => { if (!document.hidden && !lock.current) void load(); }, 5000);
    return () => { ++generation.current; ++lookupGeneration.current; window.clearInterval(timer); };
  }, [load]);

  async function perform(task: () => Promise<unknown>, message = "") {
    if (lock.current) return;
    lock.current = true; setBusy(true); setError(""); setNotice("");
    const owner = user?.id;
    try {
      await task();
      if (activeUser.current !== owner) return;
      setNotice(message); await load();
    } catch (cause) {
      if (activeUser.current === owner) setError(reason(cause));
    } finally { lock.current = false; setBusy(false); }
  }
  async function findPerson() {
    const value = identifier.trim();
    const version = ++lookupGeneration.current;
    setFound(null);
    await perform(async () => {
      const result = await service.lookup(value);
      if (version === lookupGeneration.current) setFound(result);
    });
  }
  function act(item: PersonalFriend, action: FriendAction) {
    if (["remove", "block"].includes(action) && !window.confirm(`${action === "remove" ? "Remove" : "Block"} ${item.person.name}?`)) return;
    void perform(() => service.action(item.id, action), "Your friends list has been updated.");
  }
  function matches(item: PersonalFriend, tab: View) {
    if (tab === "invitations") return false;
    return tab === "friends" ? item.status === "accepted"
      : tab === "blocked" ? item.status === "blocked" && item.blocked_by_me
      : item.status === "pending" && item.direction === tab;
  }
  const visible = items.filter((item) => matches(item, view) && `${item.person.name} ${item.person.username}`.toLowerCase().includes(search.toLowerCase()));

  if (accountLoading) return <p role="status">Loading your account…</p>;
  if (!user) return <p>Please <Link href="/login">sign in</Link> to use Friends.</p>;
  if (!user.is_email_verified) return <p role="alert">Verify your email before sending or accepting friend requests.</p>;

  return <main className="ps-page">
    <header className="ps-header">
      <div><h1>Friends</h1><p className="ps-muted">Your people, wherever you work.</p></div>
      <button className="button button--outline" disabled={busy} onClick={() => void load()}><RefreshCcw size={16} /> Refresh</button>
    </header>
    {error && <p className="ps-error" role="alert">{error}</p>}
    {notice && <p className="ps-success" role="status">{notice}</p>}
    <section className="ps-card" aria-labelledby="add-friend">
      <h2 id="add-friend"><UserPlus size={18} /> Add a friend</h2>
      <p className="ps-muted">Search with their exact username or User ID. Your username is <strong>@{user.username}</strong>.</p>
      <form className="ps-controls" onSubmit={(event) => { event.preventDefault(); void findPerson(); }}>
        <label className="ps-field">Username or User ID<input value={identifier} minLength={3} maxLength={64} required disabled={busy} placeholder="@username" onChange={(event) => { ++lookupGeneration.current; setIdentifier(event.target.value); setFound(null); }} /></label>
        <button className="button button--primary" disabled={busy || identifier.trim().length < 3}><Search size={16} /> Find person</button>
      </form>
      {found && <div className="ps-person">
        <span className="ps-avatar" aria-hidden="true"><UserAvatar userId={found.id} name={found.name} src={found.avatar_url} /></span>
        <div className="ps-personText"><strong>{found.name}</strong><span className="ps-muted">@{found.username}</span></div>
        <button className="button button--primary" disabled={busy || items.some((item) => item.person.id === found.id)} onClick={() => void perform(async () => { await service.request(found.id); setFound(null); setIdentifier(""); setView("outgoing"); }, "Request sent. You can chat once your friend accepts.")}>Send request</button>
      </div>}
    </section>
    <nav className="ps-tabs" aria-label="Friends views">{tabs.map(([tab, label]) => <button key={tab} aria-pressed={view === tab} onClick={() => setView(tab)}>{label} <span>{tab === "invitations" ? workspaceInvitations.length : items.filter((item) => matches(item, tab)).length}</span></button>)}</nav>
    {view === "invitations" ? <section className="ps-card" aria-label="Workspace invitations">
      <h2>Workspace invitations</h2><p className="ps-muted">Invitations addressed to your verified Workforce OS account.</p>
      {workspaceInvitations.length === 0 ? <div className="ps-empty"><Users size={28}/><p>No pending workspace invitations.</p></div> : <ul className="ps-list">{workspaceInvitations.map(invitation => <li key={invitation.id} className="ps-person">
        <span className="ps-avatar"><UserPlus size={22}/></span>
        <div className="ps-personText"><strong>Invitation to {invitation.workspace_name || "a workspace"}</strong><span>Workspace invitation</span><small>Role: {invitation.role_key} · Expires {new Date(invitation.expires_at).toLocaleDateString()} (new invitations expire after 3 days)</small></div>
        <div className="ps-actions"><button className="button button--primary" disabled={busy} onClick={() => void perform(async () => { await workspaceInvitationsService.respondToIncoming(invitation.id, "accept");
          await refreshWorkspaces();
          await openCreatedWorkspace(invitation.workspace_id); }, "Invitation accepted. Switch to your new workspace from the workspace selector.")}>Accept</button><button className="button button--outline" disabled={busy} onClick={() => void perform(() => workspaceInvitationsService.respondToIncoming(invitation.id, "decline"), "Invitation declined.")}>Reject</button></div>
      </li>)}</ul>}
    </section> : null}
    {view !== "invitations" && <section className="ps-card" aria-label="Friends list">
      <label className="ps-field">Search this list<input value={search} placeholder="Name or username" onChange={(event) => setSearch(event.target.value)} /></label>
      {loading ? <p role="status">Loading friends…</p> : !visible.length ? <div className="ps-empty"><Users size={28} /><h2>{search ? "No matching people" : "Nothing here yet"}</h2><p>New requests and accepted friends will appear here.</p></div> : <ul className="ps-list">{visible.map((item) => <li className="ps-person" key={item.id}>
        <span className="ps-avatar" aria-hidden="true"><UserAvatar userId={item.person.id} name={item.person.name} src={item.person.avatar_url} /></span>
        <div className="ps-personText"><strong>{item.person.name}</strong><span className="ps-muted">@{item.person.username}</span><small>{item.status === "accepted" ? item.presence : item.status === "pending" ? `${item.direction === "incoming" ? "Received" : "Sent"} request` : "Blocked"}</small></div>
        <div className="ps-actions">
          {item.status === "accepted" && <><button className="button button--primary" disabled={busy} onClick={() => void perform(async () => { const conversation = await socialChatService.createOrGetDirect(item.person.id); router.push(`/chat?conversation=${conversation.id}`); })}><MessageCircle size={15} /> Message</button><button className="button button--outline" disabled={busy} onClick={() => act(item, "remove")}>Remove</button><button className="button button--outline" disabled={busy} onClick={() => act(item, "block")}>Block</button></>}
          {item.status === "pending" && (item.direction === "incoming" ? <><button className="button button--primary" disabled={busy} onClick={() => act(item, "accept")}>Accept</button><button className="button button--outline" disabled={busy} onClick={() => act(item, "reject")}>Decline</button></> : <button className="button button--outline" disabled={busy} onClick={() => act(item, "cancel")}>Cancel request</button>)}
          {item.blocked_by_me && <button className="button button--outline" disabled={busy} onClick={() => act(item, "unblock")}>Unblock</button>}
        </div>
      </li>)}</ul>}
    </section>}
  </main>;
}
