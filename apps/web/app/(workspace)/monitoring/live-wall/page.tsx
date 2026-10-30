"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import Link from "next/link";
import { Activity, AlertTriangle, CheckCircle2, ChevronLeft, ChevronRight, Clock3, Expand, Eye, Laptop2, LoaderCircle, Monitor, Play, RefreshCcw, Search, ShieldCheck, SlidersHorizontal, Square, Users, Wifi, WifiOff, X } from "lucide-react";
import { api } from "@/lib/api/client";
import { useWorkspace } from "@/contexts/workspace-context";
import { WorkspaceRequired } from "@/components/workspace/workspace-required";
import { hasAnyPermission } from "@/lib/workspace/access";

type Device = {
  device_id: string;
  employee_id: string;
  device_name: string;
  platform: string;
  os_version: string | null;
  agent_version: string;
  status: "online" | "offline" | "disabled";
  is_online: boolean;
  screen_capability: boolean;
  live_ready: boolean;
  monitoring_ready: boolean;
  consent_granted: boolean;
  last_seen_at: string | null;
  needs_setup: boolean;
  setup_reasons: string[];
};
type Readiness = { devices: Device[]; summary: { total: number; online: number; offline: number; disabled: number; live_ready: number; needs_setup: number } };
type AgentRow = { id: string; full_name?: string; first_name?: string; last_name?: string; employee_code?: string };
type EmployeeList = { employees: AgentRow[] };
type LiveSession = { id: string; device_id: string; employee_id: string; status: string; consent_required: boolean; visible_indicator_required: boolean; session_channel: string | null; started_at: string | null; ended_at: string | null; expires_at: string; transport: string };
type Filter = "all" | "online" | "offline" | "ready" | "setup";
const PAGE_SIZE = 12;
const timeAgo = (value: string | null): string => {
  if (!value) return "Never";
  const millis = new Date(value).getTime();
  if (!Number.isFinite(millis)) return "Unknown";
  const secs = Math.max(0, Math.floor((Date.now() - millis) / 1000));
  if (secs < 60) return "Just now";
  if (secs < 3600) return `${Math.floor(secs / 60)}m ago`;
  if (secs < 86400) return `${Math.floor(secs / 3600)}h ago`;
  return new Date(millis).toLocaleDateString();
};
function Pill({ kind, children }: { kind: "green" | "gray" | "amber" | "blue"; children: ReactNode }) {
  return <span className={`lw-pill lw-${kind}`}>{children}</span>;
}
function Tile({ device, employee, selected, session, onOpen, onRequest }: {
  device: Device; employee: string; selected: boolean; session?: LiveSession;
  onOpen: () => void; onRequest: () => void;
}) {
  const isOnline = device.is_online && device.status === "online";
  const active = session?.status === "active";
  return <article className={`lw-tile ${selected ? "lw-tile-selected" : ""}`}>
    <div className="lw-preview">
      <div className="lw-preview-top"><Pill kind={active ? "blue" : isOnline ? "green" : "gray"}>{active ? "Session active" : isOnline ? "Connected" : "Offline"}</Pill><span><Monitor size={13}/>{device.platform || "Device"}</span></div>
      <div className="lw-preview-middle">{isOnline ? <Monitor size={39} strokeWidth={1.3}/> : <WifiOff size={39} strokeWidth={1.3}/>}<strong>{active ? "Session accepted" : isOnline ? "Screen preview unavailable" : "Device offline"}</strong><small>{active ? "WebRTC rendering requires the authorized signaling/receiver integration." : isOnline ? "Start an approved session to request viewing." : "Waiting for the device to reconnect."}</small></div>
      <button className="lw-preview-open" aria-label={`Open ${device.device_name} details`} type="button" onClick={onOpen}><Expand size={16}/></button>
    </div>
    <div className="lw-tile-body"><button type="button" className="lw-tile-title" onClick={onOpen}><span className="lw-avatar">{employee.trim().charAt(0).toUpperCase() || "?"}</span><span><strong>{employee}</strong><small>{device.device_name}</small></span></button><span className="lw-last">{timeAgo(device.last_seen_at)}</span></div>
    <div className="lw-tile-footer"><span>{device.live_ready ? <><CheckCircle2 size={14}/> Live-ready</> : <><AlertTriangle size={14}/> {device.needs_setup ? "Setup needed" : "Not live-ready"}</>}</span><button type="button" disabled={!device.live_ready || Boolean(session && ["requested", "pending", "active", "accepted"].includes(session.status))} onClick={onRequest}><Play size={13}/>{session ? session.status : "Request view"}</button></div>
  </article>;
}
export default function LiveScreenWallPage() {
  const { workspaceId, permissions, navigationView } = useWorkspace();
  const allowedRead = hasAnyPermission(permissions, ["monitoring.all.read", "monitoring.team.read", "monitoring.self.read"], navigationView);
  const allowedLive = hasAnyPermission(permissions, ["monitoring.live_screen"], navigationView);
  const [devices, setDevices] = useState<Device[]>([]);
  const [names, setNames] = useState<Record<string, string>>({});
  const [sessions, setSessions] = useState<Record<string, LiveSession>>({});
  const [filter, setFilter] = useState<Filter>("all");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
  const load = useCallback(async (quiet = false) => {
    if (!workspaceId || !allowedRead) { setLoading(false); return; }
    if (quiet) setRefreshing(true); else setLoading(true);
    try {
      const response = await api.get<Readiness>(`/workspaces/${workspaceId}/devices/readiness`);
      setDevices(response.devices ?? []);
      setLastRefresh(new Date());
      setError("");
      // The employee-directory endpoint may be unavailable to monitoring-only roles.
      try {
        const people = await api.get<EmployeeList>(`/workspaces/${workspaceId}/employees?include_inactive=true`);
        setNames(Object.fromEntries((people.employees ?? []).map(person => [person.id, person.full_name?.trim() || [person.first_name, person.last_name].filter(Boolean).join(" ") || person.employee_code || "Employee"])));
      } catch { setNames({}); }
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Could not load device readiness."); }
    finally { setLoading(false); setRefreshing(false); }
  }, [workspaceId, allowedRead]);
  useEffect(() => { void load(); }, [load]);
  useEffect(() => {
    if (!workspaceId || !allowedRead) return;
    const timer = window.setInterval(() => { if (document.visibilityState === "visible") void load(true); }, 30000);
    return () => window.clearInterval(timer);
  }, [workspaceId, allowedRead, load]);
  const getName = (device: Device) => names[device.employee_id] || `Employee ${device.employee_id.slice(0, 8)}`;
  const filtered = useMemo(() => devices.filter(device => {
    const online = device.status === "online" && device.is_online;
    if (filter === "online" && !online) return false;
    if (filter === "offline" && online) return false;
    if (filter === "ready" && !device.live_ready) return false;
    if (filter === "setup" && !device.needs_setup) return false;
    return `${device.device_name} ${device.platform} ${getName(device)}`.toLowerCase().includes(search.trim().toLowerCase());
  }).sort((a, b) => Number(b.is_online) - Number(a.is_online) || a.device_name.localeCompare(b.device_name)), [devices, filter, search, names]);
  const pages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const safePage = Math.min(page, pages);
  const shown = filtered.slice((safePage - 1) * PAGE_SIZE, safePage * PAGE_SIZE);
  const selected = devices.find(device => device.device_id === selectedId) || null;
  const onlineCount = devices.filter(d => d.is_online && d.status === "online").length;
  const readyCount = devices.filter(d => d.live_ready).length;
  const sessionCount = Object.values(sessions).filter(s => ["requested", "pending", "accepted", "active"].includes(s.status)).length;
  const requestSession = async (device: Device) => {
    if (!workspaceId || !allowedLive || !device.live_ready) return;
    setBusyId(device.device_id); setError(""); setNotice("");
    try {
      const session = await api.post<LiveSession>(`/workspaces/${workspaceId}/live-monitoring/live-sessions`, { device_id: device.device_id, reason: "Authorized live-screen wall view request" });
      setSessions(old => ({ ...old, [device.device_id]: session }));
      setSelectedId(device.device_id);
      setNotice("Session requested. The agent must accept and display its screen-sharing indicator before any viewing can begin.");
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Live-session request failed."); }
    finally { setBusyId(null); }
  };
  const pollSession = useCallback(async (deviceId: string, sessionId: string) => {
    if (!workspaceId) return;
    try {
      const current = await api.get<LiveSession>(`/workspaces/${workspaceId}/live-monitoring/live-sessions/${sessionId}`);
      setSessions(old => ({ ...old, [deviceId]: current }));
    } catch { /* Readiness will continue to refresh; no fabricated session state. */ }
  }, [workspaceId]);
  useEffect(() => {
    const ongoing = Object.entries(sessions).filter(([, s]) => ["requested", "pending", "accepted", "active"].includes(s.status));
    if (!ongoing.length) return;
    const timer = window.setInterval(() => { if (document.visibilityState === "visible") ongoing.forEach(([id, s]) => { void pollSession(id, s.id); }); }, 5000);
    return () => window.clearInterval(timer);
  }, [sessions, pollSession]);
  const stopSession = async (deviceId: string, sessionId: string) => {
    if (!workspaceId || !allowedLive) return;
    setBusyId(deviceId); setError("");
    try {
      const stopped = await api.post<LiveSession>(`/workspaces/${workspaceId}/live-monitoring/live-sessions/${sessionId}/end`, { reason: "Stopped by authorized wall viewer" });
      setSessions(old => ({ ...old, [deviceId]: stopped }));
      setNotice("Live-session request ended.");
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Could not end session."); }
    finally { setBusyId(null); }
  };
  return <WorkspaceRequired><main className="lw-page">
    <header className="lw-header"><div><h1>Live Screen Wall</h1><p>View device availability and manage consent-based live-screen requests across your workspace.</p></div><div className="lw-actions"><Link href="/monitoring/devices" className="lw-btn lw-light"><Laptop2 size={16}/> Devices</Link><button type="button" className="lw-btn lw-dark" disabled={refreshing || !allowedRead} onClick={() => void load(true)}>{refreshing ? <LoaderCircle className="lw-spin" size={16}/> : <RefreshCcw size={16}/>} Refresh</button></div></header>
    {!allowedRead ? <div className="lw-error"><AlertTriangle size={18}/>Monitoring read permission is required.</div> : <>
      {error && <div className="lw-error"><AlertTriangle size={18}/><span>{error}</span><button type="button" onClick={() => void load()}>Retry</button></div>}
      {notice && <div className="lw-info"><ShieldCheck size={18}/>{notice}<button type="button" onClick={() => setNotice("")} aria-label="Dismiss notice"><X size={16}/></button></div>}
      <section className="lw-stats"><div><span className="lw-stat-icon"><Monitor size={25}/></span><p>Total devices<strong>{devices.length}</strong><small>Registered in device readiness</small></p></div><div><span className="lw-stat-icon lw-green"><Wifi size={25}/></span><p>Connected<strong>{onlineCount}</strong><small>Online by heartbeat</small></p></div><div><span className="lw-stat-icon lw-gold"><ShieldCheck size={25}/></span><p>Live-ready<strong>{readyCount}</strong><small>Capabilities and consent ready</small></p></div><div><span className="lw-stat-icon lw-blue"><Eye size={25}/></span><p>Session requests<strong>{sessionCount}</strong><small>Requested or ongoing here</small></p></div></section>
      <div className="lw-panel"><div className="lw-toolbar"><div className="lw-toolbar-title"><h2><Monitor size={20}/> Device screen wall</h2><span>{filtered.length} devices</span></div><div className="lw-tools"><label className="lw-search"><Search size={16}/><input aria-label="Search devices" value={search} onChange={event => { setSearch(event.target.value); setPage(1); }} placeholder="Search employee or device"/></label><label className="lw-filter"><SlidersHorizontal size={16}/><select aria-label="Filter devices" value={filter} onChange={event => { setFilter(event.target.value as Filter); setPage(1); }}><option value="all">All devices</option><option value="online">Online</option><option value="offline">Offline</option><option value="ready">Live-ready</option><option value="setup">Setup needed</option></select></label></div></div>
      {!allowedLive && <div className="lw-soft-warning"><ShieldCheck size={17}/>You can view readiness, but starting a live screen session requires the monitoring.live_screen permission.</div>}
      {loading ? <div className="lw-empty"><LoaderCircle size={32} className="lw-spin"/><strong>Loading connected devices...</strong></div> : shown.length ? <div className="lw-grid">{shown.map(device => <Tile key={device.device_id} device={device} employee={getName(device)} selected={selectedId === device.device_id} session={sessions[device.device_id]} onOpen={() => setSelectedId(device.device_id)} onRequest={() => void requestSession(device)}/>)}</div> : <div className="lw-empty"><Monitor size={38}/><strong>{devices.length ? "No devices match the filters" : "No enrolled devices found"}</strong><p>{devices.length ? "Adjust your search or selected device status." : "Install and enroll a desktop agent, then confirm that monitoring and screen-sharing capabilities are enabled."}</p><Link href="/monitoring/devices" className="lw-btn lw-dark">View device setup</Link></div>}
      <footer className="lw-bottom"><span>Showing {filtered.length ? (safePage - 1) * PAGE_SIZE + 1 : 0}–{Math.min(safePage * PAGE_SIZE, filtered.length)} of {filtered.length}</span><div><button type="button" disabled={safePage <= 1} onClick={() => setPage(p => Math.max(1, p - 1))} aria-label="Previous"><ChevronLeft size={16}/></button><span>Page {safePage} of {pages}</span><button type="button" disabled={safePage >= pages} onClick={() => setPage(p => Math.min(pages, p + 1))} aria-label="Next"><ChevronRight size={16}/></button></div></footer></div>
      <p className="lw-note"><Clock3 size={15}/>Device readiness automatically refreshes every 30 seconds. {lastRefresh ? `Last refreshed ${lastRefresh.toLocaleTimeString()}. ` : ""}Screen tiles are status placeholders, not screenshots or video streams. Live video requires a separate approved WebRTC signaling and renderer integration.</p>
    </>}
    {selected && <div className="lw-overlay" onMouseDown={e => { if (e.target === e.currentTarget) setSelectedId(null); }}><section className="lw-dialog" role="dialog" aria-modal="true" aria-labelledby="lw-title"><div className="lw-dialog-head"><div><h2 id="lw-title">{getName(selected)}</h2><p>{selected.device_name} · {selected.platform}</p></div><button type="button" onClick={() => setSelectedId(null)} aria-label="Close"><X size={20}/></button></div><div className="lw-focus"><Monitor size={53}/><strong>Live video not connected</strong><p>{sessions[selected.device_id]?.status === "active" ? "The session is active, but this application does not yet have a WebRTC renderer or signaling channel connected." : "Device previews require an employee-approved live session and a secure screen-stream receiver."}</p></div><div className="lw-dialog-info"><div><span>Readiness</span><strong>{selected.live_ready ? "Ready for request" : "Not ready"}</strong></div><div><span>Connection</span><strong>{selected.is_online ? "Online" : "Offline"}</strong></div><div><span>Employee consent</span><strong>{selected.consent_granted ? "Recorded" : "Not recorded"}</strong></div><div><span>Last heartbeat</span><strong>{timeAgo(selected.last_seen_at)}</strong></div><div><span>Session status</span><strong>{sessions[selected.device_id]?.status || "No session"}</strong></div><div><span>Session transport</span><strong>{sessions[selected.device_id]?.transport || "—"}</strong></div></div>{selected.setup_reasons?.length > 0 && <p className="lw-setup"><AlertTriangle size={16}/>{selected.setup_reasons.join(", ")}</p>}<div className="lw-dialog-actions"><button type="button" className="lw-btn lw-light" onClick={() => setSelectedId(null)}>Close</button>{sessions[selected.device_id] && ["requested", "pending", "accepted", "active"].includes(sessions[selected.device_id]?.status ?? "") ? <button type="button" className="lw-btn lw-stop" disabled={busyId === selected.device_id} onClick={() => { const currentSession = sessions[selected.device_id]; if (currentSession) void stopSession(selected.device_id, currentSession.id); }}><Square size={14}/> End session</button> : <button type="button" className="lw-btn lw-dark" disabled={!allowedLive || !selected.live_ready || busyId === selected.device_id} onClick={() => void requestSession(selected)}>{busyId === selected.device_id ? <LoaderCircle size={15} className="lw-spin"/> : <Play size={15}/>}Request live view</button>}</div></section></div>}
    <style jsx global>{`
      .lw-page{--ink:#10213a;--muted:#718198;--border:#e4e8ed;color:var(--ink);background:#fbfaf8;min-height:100%;padding:23px;font-size:13px}.lw-page *{box-sizing:border-box}.lw-page button,.lw-page input,.lw-page select{font:inherit}.lw-page button{cursor:pointer}.lw-page button:disabled{opacity:.45;cursor:not-allowed}.lw-header,.lw-actions,.lw-toolbar,.lw-toolbar-title,.lw-tools,.lw-bottom,.lw-bottom>div,.lw-dialog-head,.lw-dialog-actions{display:flex;align-items:center;justify-content:space-between;gap:12px}.lw-header{margin-bottom:20px;flex-wrap:wrap}.lw-header h1{margin:0;font-size:30px;letter-spacing:-.8px;font-weight:750}.lw-header p{color:var(--muted);margin:7px 0 0;font-size:14px}.lw-actions{justify-content:flex-end}.lw-btn{min-height:39px;border-radius:8px;display:inline-flex;align-items:center;justify-content:center;gap:8px;padding:0 14px;text-decoration:none;font-weight:650!important}.lw-dark{background:#1a293a;border:1px solid #1a293a;color:white}.lw-light{background:white;border:1px solid #dbe1e8;color:var(--ink)}.lw-stop{background:#fff0ee;border:1px solid #f2ccc6;color:#b83c30}.lw-stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:13px;margin-bottom:16px}.lw-stats>div{background:#fffefa;border:1px solid var(--border);border-radius:12px;padding:18px;display:flex;align-items:center;gap:15px;min-width:0}.lw-stat-icon{width:55px;height:55px;flex-shrink:0;border-radius:50%;display:grid;place-items:center;color:#4c6da8;background:#eaf1fb}.lw-stat-icon.lw-green{color:#15a468;background:#e0f7ea}.lw-stat-icon.lw-gold{color:#d2940a;background:#fff1cd}.lw-stat-icon.lw-blue{color:#4c70d1;background:#e8eeff}.lw-stats p{display:flex;flex-direction:column;gap:4px;margin:0;min-width:0;font-weight:600}.lw-stats strong{font-size:27px;line-height:1.1;letter-spacing:-.7px}.lw-stats small{font-size:11px;color:var(--muted);font-weight:400}.lw-panel{background:#fffefa;border:1px solid var(--border);border-radius:12px;overflow:hidden}.lw-toolbar{min-height:71px;padding:15px 18px;flex-wrap:wrap;border-bottom:1px solid var(--border)}.lw-toolbar-title{justify-content:flex-start}.lw-toolbar-title h2{font-size:18px;margin:0;display:flex;align-items:center;gap:10px}.lw-toolbar-title>span{color:var(--muted)}.lw-tools{justify-content:flex-end;flex-wrap:wrap}.lw-search,.lw-filter{height:37px;border:1px solid #dfe4eb;border-radius:8px;background:white;display:flex;align-items:center;gap:8px;padding:0 11px;color:#697a91}.lw-search input{border:0;outline:0;background:transparent;width:190px;min-width:0;color:var(--ink)}.lw-filter select{border:0;outline:0;background:transparent;color:var(--ink)}.lw-grid{padding:17px;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}.lw-tile{border:1px solid #e1e5e9;border-radius:11px;background:white;overflow:hidden;min-width:0}.lw-tile-selected{border-color:#dcb55a;box-shadow:0 0 0 1px #f4ddaa}.lw-preview{aspect-ratio:16/9;position:relative;background:linear-gradient(140deg,#1c2839,#101723);color:#aebbd0}.lw-preview-top{position:absolute;inset:12px 12px auto;display:flex;align-items:center;justify-content:space-between;gap:7px;z-index:1}.lw-preview-top>span:last-child{display:flex;align-items:center;gap:5px;font-size:11px;color:#c2ccdc}.lw-pill{border-radius:20px;padding:5px 9px;font-size:10px;font-weight:700;display:inline-flex}.lw-green{background:#e1f7e9;color:#12824e}.lw-gray{background:#e4e8ed;color:#526074}.lw-amber{background:#fff1cf;color:#9b700d}.lw-blue{background:#e4edff;color:#345ec3}.lw-preview-middle{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:8px;padding:45px 24px 20px;text-align:center}.lw-preview-middle strong{font-size:13px;color:#e4eaf5}.lw-preview-middle small{font-size:11px;max-width:270px;line-height:1.5}.lw-preview-open{position:absolute;bottom:10px;right:10px;border:1px solid #66758c;background:#233348;color:white;width:29px;height:29px;display:grid;place-items:center;border-radius:7px}.lw-tile-body{display:flex;justify-content:space-between;gap:7px;align-items:center;padding:12px}.lw-tile-title{display:flex;align-items:center;gap:9px;border:0;background:transparent;text-align:left;min-width:0;color:var(--ink)}.lw-tile-title>span:last-child{display:flex;flex-direction:column;gap:4px;min-width:0}.lw-tile-title strong{font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.lw-tile-title small{color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:190px}.lw-avatar{width:32px;height:32px;flex-shrink:0;display:grid;place-items:center;background:#fff0ca;border-radius:50%;color:#a57913;font-weight:800}.lw-last{font-size:10px;color:var(--muted);white-space:nowrap}.lw-tile-footer{padding:10px 12px;border-top:1px solid #ecedf0;display:flex;justify-content:space-between;align-items:center;gap:7px}.lw-tile-footer>span{color:#758096;font-size:11px;display:flex;align-items:center;gap:5px}.lw-tile-footer button{border:1px solid #dfe4e8;border-radius:6px;padding:6px 8px;background:#fff;color:#172a42;display:flex;align-items:center;gap:5px;font-size:11px}.lw-bottom{padding:14px 18px;color:var(--muted);border-top:1px solid #ecedf0}.lw-bottom>div{gap:10px}.lw-bottom button{border:1px solid #e0e4eb;background:white;display:grid;place-items:center;height:31px;width:31px;border-radius:7px}.lw-empty{min-height:340px;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:12px;text-align:center;padding:25px;color:#8291a6}.lw-empty strong{color:var(--ink);font-size:16px}.lw-empty p{max-width:380px;line-height:1.6;margin:0}.lw-note{display:flex;align-items:flex-start;gap:9px;color:var(--muted);font-size:12px;line-height:1.6;margin:15px 0}.lw-error,.lw-info,.lw-soft-warning{display:flex;align-items:center;gap:10px;padding:12px 14px;border-radius:8px;margin-bottom:14px}.lw-error{border:1px solid #efbcbc;background:#fff1f1;color:#a72d30}.lw-info{border:1px solid #b9dfd1;background:#ecf9f4;color:#15784d}.lw-soft-warning{background:#fff8e8;color:#8f670f;margin:12px 17px 0;border:1px solid #f1e3c1}.lw-error span{flex:1}.lw-error button,.lw-info button{margin-left:auto;border:0;background:transparent}.lw-overlay{position:fixed;inset:0;background:#0715269c;z-index:250;display:grid;place-items:center;padding:18px}.lw-dialog{width:min(760px,100%);max-height:92vh;overflow:auto;background:#fffefa;border-radius:14px;box-shadow:0 25px 80px #0005}.lw-dialog-head{padding:17px 20px}.lw-dialog-head h2{font-size:21px;margin:0}.lw-dialog-head p{margin:5px 0 0;color:var(--muted)}.lw-dialog-head button{border:0;background:transparent}.lw-focus{background:linear-gradient(130deg,#202d41,#0d1725);color:#b9c5d8;min-height:270px;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:13px;text-align:center;padding:25px}.lw-focus strong{font-size:17px;color:#fff}.lw-focus p{max-width:410px;line-height:1.6;margin:0}.lw-dialog-info{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:0 20px;padding:12px 20px}.lw-dialog-info>div{padding:11px 0;border-bottom:1px solid #e7eaf0;display:flex;justify-content:space-between;gap:12px}.lw-dialog-info span{color:var(--muted)}.lw-dialog-info strong{text-align:right}.lw-setup{display:flex;gap:8px;align-items:center;margin:0 20px 10px;padding:11px;background:#fff5dc;color:#9c6c06;border-radius:7px;line-height:1.5}.lw-dialog-actions{justify-content:flex-end;padding:14px 20px 20px}.lw-spin{animation:lw-spin 1s linear infinite}@keyframes lw-spin{to{transform:rotate(360deg)}}@media(max-width:1300px){.lw-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:900px){.lw-stats{grid-template-columns:repeat(2,minmax(0,1fr))}.lw-grid{grid-template-columns:1fr}}@media(max-width:640px){.lw-page{padding:14px}.lw-stats{grid-template-columns:1fr}.lw-tools{justify-content:flex-start;width:100%}.lw-search{flex:1}.lw-search input{width:100%}.lw-dialog-info{grid-template-columns:1fr}.lw-toolbar{align-items:flex-start}.lw-header h1{font-size:24px}}
    `}</style>
  </main></WorkspaceRequired>;
}
