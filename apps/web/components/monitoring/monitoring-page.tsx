"use client";

import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, BarChart3, CheckCircle2, Clock3, Download, Laptop2, Monitor, RefreshCw, Search, Users } from "lucide-react";
import { useWorkspace } from "@/contexts/workspace-context";
import { WorkspaceRequired } from "@/components/workspace/workspace-required";
import { hasAnyPermission } from "@/lib/workspace/access";
import { monitoringService, type MonitoringSnapshot } from "@/services/monitoring.service";

type Section = "overview" | "employees" | "devices" | "live-screen" | "live-wall" | "screenshots" | "activity" | "applications" | "websites" | "attendance" | "alerts" | "reports";
const titles: Record<Section, { title: string; description: string }> = {
  overview: { title: "Monitoring Overview", description: "Device and employee monitoring status across your organization." },
  employees: { title: "Employee Monitoring", description: "View employee device status, activity and monitoring readiness." },
  devices: { title: "Monitoring Devices", description: "Manage connected devices, agent health and enrollment status." },
  "live-screen": { title: "Live Screen", description: "View one authorized live screen session in real time." },
  "live-wall": { title: "Live Screen Wall", description: "View active, employee-shared screens across your team." },
  screenshots: { title: "Screenshots", description: "Review authorized screenshots captured by your monitoring policy." },
  activity: { title: "Activity Timeline", description: "Review time, signal and work activity collected from authorized agents." },
  applications: { title: "Application Activity", description: "See application usage and active time by employee or device." },
  websites: { title: "Website Activity", description: "Review website activity collected under your workspace policy." },
  attendance: { title: "Monitoring Attendance", description: "Reconcile attendance with device and agent signals." },
  alerts: { title: "Monitoring Alerts", description: "Monitor and manage device and employee alerts." },
  reports: { title: "Monitoring Reports", description: "Generate reports on device and employee activity." },
};
const loaders: Record<Section, (id: string, q?: string) => Promise<MonitoringSnapshot>> = {
  overview: monitoringService.overview, employees: monitoringService.employees, devices: monitoringService.devices, "live-screen": monitoringService.liveWall,
  "live-wall": monitoringService.liveWall, screenshots: monitoringService.screenshots, activity: monitoringService.activity,
  applications: monitoringService.applications, websites: monitoringService.websites, attendance: monitoringService.attendance,
  alerts: monitoringService.alerts, reports: monitoringService.reports,
};
const fallbackKeys: Record<Section, string[]> = {
  overview: ["employees", "online", "idle", "offline"], employees: ["name", "department", "device", "status", "last_signal"], devices: ["name", "employee", "platform", "status", "last_heartbeat"], "live-screen": ["employee", "device", "status", "source", "last_update"],
  "live-wall": ["employee", "department", "device", "status", "source"], screenshots: ["employee", "captured_at", "device", "review_status"], activity: ["employee", "started_at", "duration", "status"],
  applications: ["application", "employee", "active_time", "last_seen"], websites: ["website", "employee", "active_time", "category"], attendance: ["employee", "scheduled", "tracked", "variance"], alerts: ["title", "severity", "status", "device", "created_at"], reports: ["name", "period", "status", "format"],
};

function label(key: string) { return key.replaceAll("_", " ").replace(/\b\w/g, c => c.toUpperCase()); }
function value(row: Record<string, unknown>, key: string) { const v = row[key]; return v === null || v === undefined || v === "" ? "—" : String(v); }

export function MonitoringPage({ section }: { section: Section }) {
  const { workspaceId, permissions, navigationView } = useWorkspace();
  const [data, setData] = useState<MonitoringSnapshot | null>(null);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const allowed = hasAnyPermission(permissions, ["monitoring.all.read", "monitoring.team.read", "monitoring.self.read", "reports.all.read", "reports.team.read", "reports.self.read"], navigationView);
  const meta = titles[section];
  const columns = fallbackKeys[section];
  const rows = useMemo(() => Array.isArray(data?.items) ? data.items : [], [data]);
  const load = () => {
    if (!workspaceId || !allowed) { setLoading(false); return; }
    setLoading(true); setError("");
    const encoded = query.trim() ? `?search=${encodeURIComponent(query.trim())}` : "";
    loaders[section](workspaceId, encoded).then(setData).catch(cause => setError(cause instanceof Error ? cause.message : "Monitoring data could not be loaded.")).finally(() => setLoading(false));
  };
  useEffect(load, [workspaceId, section, allowed]);
  return <WorkspaceRequired><main className="monitoring-page">
    <header className="monitoring-header"><div><p className="eyebrow">Workspace / Monitoring</p><h1>{meta.title}</h1><p>{meta.description}</p></div><div className="header-actions"><button type="button" onClick={load}><RefreshCw size={16} />Refresh</button>{section === "reports" && <button type="button" className="dark"><Download size={16} />Generate report</button>}</div></header>
    {!allowed ? <div className="notice"><AlertTriangle size={18} />You do not have permission to view monitoring data.</div> : <>
      <section className="metric-grid">{(data?.summary ? Object.entries(data.summary).slice(0, 4) : [["Total", data?.total ?? "—"], ["Online", "—"], ["Idle", "—"], ["Offline", "—"]]).map(([key, val]) => <article className="metric" key={String(key)}><span className="metric-icon"><Users size={20} /></span><strong>{String(val)}</strong><span>{label(String(key))}</span></article>)}</section>
      <section className="panel"><div className="panel-head"><h2>{section === "overview" ? "Employee status and monitoring health" : `${meta.title} records`}</h2><label className="search"><Search size={16} /><input value={query} onChange={e => setQuery(e.target.value)} onKeyDown={e => e.key === "Enter" && load()} placeholder="Search employees..." /></label></div>
        {error && <div className="notice error"><AlertTriangle size={18} />{error}<button type="button" onClick={load}>Retry</button></div>}
        {loading ? <div className="empty"><RefreshCw className="spin" size={24} />Loading authorized monitoring data…</div> : rows.length ? <div className="table-wrap"><table><thead><tr>{columns.map(column => <th key={column}>{label(column)}</th>)}</tr></thead><tbody>{rows.map((row, index) => <tr key={String(row.id ?? index)}>{columns.map(column => <td key={column}>{value(row, column)}</td>)}</tr>)}</tbody></table></div> : <div className="empty"><CheckCircle2 size={28} /><strong>No monitoring records returned</strong><span>Connect an authorized desktop agent or browser extension to begin collecting workspace data.</span></div>}
      </section>
    </>}
    <style jsx>{`.monitoring-page{padding:clamp(18px,3vw,32px);color:var(--color-text-primary,#11203b);background:#fbfaf6;min-height:100%;}.monitoring-header{display:flex;justify-content:space-between;gap:20px;align-items:flex-end;margin-bottom:22px}.eyebrow{font-size:13px;color:#64748b;margin:0 0 8px}.monitoring-header h1{margin:0;font-size:clamp(26px,3vw,36px);letter-spacing:-.04em}.monitoring-header p:not(.eyebrow){margin:8px 0 0;color:#64748b}.header-actions{display:flex;gap:10px;flex-wrap:wrap}.header-actions button,.notice button{display:inline-flex;align-items:center;gap:8px;border:1px solid #dbe1e9;background:#fff;border-radius:9px;padding:10px 14px;color:#17243b;cursor:pointer}.header-actions .dark{background:#172534;color:#fff;border-color:#172534}.metric-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin-bottom:16px}.metric,.panel{background:#fffdf8;border:1px solid #e7e3d9;border-radius:14px;box-shadow:0 3px 18px #22344b08}.metric{padding:18px;display:grid;grid-template-columns:auto 1fr;column-gap:12px;align-items:center}.metric-icon{grid-row:span 2;border-radius:50%;padding:12px;background:#fff0bd;color:#9a6400}.metric strong{font-size:25px}.metric span:last-child{color:#64748b;font-size:13px;text-transform:capitalize}.panel{padding:16px}.panel-head{display:flex;justify-content:space-between;align-items:center;gap:16px;margin-bottom:12px}.panel h2{font-size:18px;margin:0}.search{display:flex;align-items:center;gap:7px;border:1px solid #dbe1e9;background:#fff;border-radius:9px;padding:9px 11px;color:#64748b}.search input{border:0;outline:0;min-width:190px;color:#17243b;background:transparent}.table-wrap{overflow-x:auto}table{width:100%;border-collapse:collapse;min-width:680px}th,td{text-align:left;padding:13px 10px;border-top:1px solid #ece9e1;font-size:13px}th{font-size:12px;color:#64748b;text-transform:capitalize}.empty{min-height:180px;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:9px;color:#64748b;text-align:center}.empty strong{color:#17243b}.notice{display:flex;align-items:center;gap:10px;padding:14px 16px;border:1px solid #f1d798;background:#fff8dd;border-radius:11px;margin-bottom:14px}.notice.error{border-color:#f1b8b8;background:#fff2f2}.notice button{margin-left:auto;padding:6px 10px}.spin{animation:spin 1s linear infinite}@keyframes spin{to{transform:rotate(360deg)}}@media(max-width:800px){.monitoring-header{align-items:flex-start;flex-direction:column}.metric-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.panel-head{align-items:flex-start;flex-direction:column;width:100%}.search{width:100%}.search input{width:100%}}@media(max-width:450px){.metric-grid{grid-template-columns:1fr}.monitoring-page{padding:16px}}`}</style>
  </main></WorkspaceRequired>;
}
