"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Search, Users, UserPlus } from "lucide-react";
import { api } from "@/lib/api/client";
import { useWorkspace } from "@/contexts/workspace-context";
import { WorkspaceRequired } from "@/components/workspace/workspace-required";
import { getWorkspaceTemplate } from "@/lib/workspace/templates";
import { hasAnyPermission } from "@/lib/workspace/access";

interface Member { id: string; name: string; email: string; role: string; status: string; account_active: boolean; joined_at: string | null; }
interface Directory { items: Member[]; total: number; page: number; page_size: number; }

export function WorkspaceDirectory({ clients = false }: { clients?: boolean }) {
  const { workspaceId, workspace, permissions, navigationView } = useWorkspace();
  const [query, setQuery] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [retry, setRetry] = useState(0);
  const [data, setData] = useState<Directory | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const words = getWorkspaceTemplate(workspace?.workspace_type);
  const canRead = hasAnyPermission(permissions, ["members.read"], navigationView);
  const canInvite = hasAnyPermission(permissions, ["members.invite"], navigationView);
  useEffect(() => { const timer = window.setTimeout(() => { setPage(1); setSearch(query.trim()); }, 250); return () => window.clearTimeout(timer); }, [query]);
  useEffect(() => {
    setData(null); setError(""); setLoading(true);
    if (!workspaceId || !canRead) { setLoading(false); return; }
    let stopped = false;
    const params = new URLSearchParams({ page: String(page), page_size: "25", search, clients_only: String(clients) });
    api.get<Directory>(`/workspaces/${workspaceId}/directory?${params}`).then(result => {
      if (!stopped) setData(result);
    }).catch(cause => { if (!stopped) setError(cause instanceof Error ? cause.message : "The directory could not be loaded."); })
      .finally(() => { if (!stopped) setLoading(false); });
    return () => { stopped = true; };
  }, [workspaceId, canRead, clients, page, search, retry]);
  return <WorkspaceRequired><main className="directory">
    <header><div><h1>{clients ? words.clients : words.members}</h1><p>{clients ? "Workspace accounts assigned the client role." : "The people who belong to this workspace."}</p></div>
      {canInvite && <Link className="action" href="/invitations"><UserPlus size={17} />{clients ? "Invite client" : "Invite members"}</Link>}</header>
    {!canRead ? <p role="status">You do not have permission to view the workspace directory.</p> : <>
      <label className="search"><Search size={17} /><input aria-label="Search workspace directory" type="search" maxLength={80} value={query} onChange={event => setQuery(event.target.value)} placeholder="Search name or email" /></label>
      {error && <div role="alert"><p>{error}</p><button onClick={() => setRetry(value => value + 1)} type="button">Retry</button></div>}
      <section aria-busy={loading} className="table-wrap">
        {loading ? <p role="status">Loading directory…</p> : data?.items.length ? <table><thead><tr><th>Name</th><th>Email</th><th>Role</th><th>Status</th><th>Joined</th></tr></thead><tbody>{data.items.map(member => <tr key={member.id}>
          <td><strong>{member.name}</strong></td><td>{member.email}</td><td>{member.role.replaceAll("_", " ")}</td><td>{member.account_active ? member.status : "Account disabled"}</td><td>{member.joined_at ? new Intl.DateTimeFormat("en-GB", { dateStyle: "medium" }).format(new Date(member.joined_at)) : "—"}</td>
        </tr>)}</tbody></table> : !error && <div className="empty"><Users size={30} /><h2>{search ? "No matching accounts" : clients ? "No client accounts yet" : "No members found"}</h2><p>{search ? "Try a different name or email." : clients ? "Client-role members will appear here after they join your workspace." : "Workspace members will appear here."}</p></div>}
      </section>
      {data && data.total > 0 && <footer><span>{data.total} {clients ? "client accounts" : "members"}</span><div><button type="button" disabled={page === 1 || loading} onClick={() => setPage(value => value - 1)}>Previous</button><span>Page {page} of {Math.max(1, Math.ceil(data.total / data.page_size))}</span><button type="button" disabled={loading || page * data.page_size >= data.total} onClick={() => setPage(value => value + 1)}>Next</button></div></footer>}
    </>}
    <style jsx>{`
      .directory { padding: clamp(16px, 3vw, 30px); color: var(--color-text-primary, #17202a); }
      header, footer, footer div { display: flex; align-items: center; justify-content: space-between; gap: 16px; flex-wrap: wrap; }
      h1 { margin: 0 0 8px; font-size: 28px; letter-spacing: -.025em; } header p { color: var(--color-text-secondary, #626b76); margin: 0; }
      .search { display: flex; align-items: center; gap: 10px; margin-block: 24px; max-width: 420px; padding: 10px 12px; border: 1px solid var(--color-border, #e6dfd2); border-radius: 8px; background: var(--color-panel-background, #fffefa); }
      input { width: 100%; border: 0; outline: 0; background: transparent; color: inherit; font: inherit; font-size: 16px; } .search:focus-within { outline: 2px solid #ac7500; outline-offset: 2px; }
      .table-wrap { overflow: auto; background: var(--color-panel-background, #fffefa); border: 1px solid var(--color-border, #e6dfd2); border-radius: 12px; }
      table { border-collapse: collapse; width: 100%; min-width: 660px; text-align: start; } th, td { padding: 15px; border-bottom: 1px solid var(--color-border, #e6dfd2); font-size: 13px; } th { background: var(--color-app-background, #f8f6f1); color: inherit; }
      .empty { display: grid; justify-items: center; text-align: center; padding: 48px 20px; } .empty h2 { font-size: 18px; } .empty p { max-width: 45ch; color: var(--color-text-secondary, #626b76); }
      button { padding: 9px 14px; font: inherit; border: 1px solid var(--color-border, #e6dfd2); border-radius: 7px; background: var(--color-panel-background, #fffefa); color: inherit; cursor: pointer; } button:disabled { opacity: .5; cursor: not-allowed; } footer { padding-block: 16px; font-size: 13px; }
      :global(.directory .action) { display: inline-flex; align-items: center; gap: 8px; color: white; background: #242c32; padding: 11px 16px; text-decoration: none; border-radius: 8px; }
    `}</style>
  </main></WorkspaceRequired>;
}
