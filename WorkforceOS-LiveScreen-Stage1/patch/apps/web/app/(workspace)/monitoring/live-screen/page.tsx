"use client";

import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  useRef,
} from "react";
import {
  Activity,
  AlertCircle,
  CheckCircle2,
  Clock3,
  Laptop2,
  Monitor,
  MonitorPlay,
  Play,
  RefreshCw,
  ShieldCheck,
  Square,
  Users,
  Wifi,
  WifiOff,
  Maximize2,
  Pause,
  Eye,
  Settings2,
} from "lucide-react";

import { useWorkspace } from "@/contexts/workspace-context";
import { api } from "@/lib/api/client";
import { WorkspaceRequired } from "@/components/workspace/workspace-required";

import {
  employeesService,
  type Employee,
} from "@/services/employees.service";

import {
  deviceManagementService,
} from "@/services/device-management.service";

import {
  monitoringControlService,
} from "@/services/monitoring-control.service";

import {
  monitoringService,
  type MonitoringSnapshot,
} from "@/services/monitoring.service";

import type {
  DevicePublic,
} from "@/types/device-management";

type DesktopAgentDevice = {
  id: string;
  employee_id: string;
  device_name: string;
  status: string;
  is_disabled: boolean;
  last_seen_at: string | null;
};

type DesktopAgentList = { items: DesktopAgentDevice[]; total: number };
type DesktopAgentCapabilities = { live_screen: boolean };

function isDesktopOnline(device: DesktopAgentDevice): boolean {
  if (device.is_disabled || device.status !== "online" || !device.last_seen_at) return false;
  const timestamp = new Date(device.last_seen_at).getTime();
  const elapsed = Date.now() - timestamp;
  return Number.isFinite(elapsed) && elapsed >= 0 && elapsed < 120_000;
}

type SessionInfo = {
  sessionId: string;
  employeeId: string;
  deviceId: string;
  status: string;
};

function messageFromError(error: unknown): string {
  return error instanceof Error
    ? error.message
    : "The request could not be completed.";
}

function formatDate(value: string | null): string {
  if (!value) return "Never";

  const date = new Date(value);

  return Number.isNaN(date.getTime())
    ? value
    : date.toLocaleString();
}

function isOnline(device: DevicePublic): boolean {
  if (!device.is_active || device.status !== "active") {
    return false;
  }

  if (!device.last_seen_at) return false;

  const lastSeen = new Date(device.last_seen_at).getTime();

  return (
    Number.isFinite(lastSeen) &&
    Date.now() - lastSeen < 120_000
  );
}

export default function LiveScreenPage() {
  const { workspaceId } = useWorkspace();

  const [employees, setEmployees] = useState<Employee[]>([]);
  const [devices, setDevices] = useState<DevicePublic[]>([]);
  const [desktopAgents, setDesktopAgents] = useState<DesktopAgentDevice[]>([]);
  const [desktopDeviceId, setDesktopDeviceId] = useState("");
  const [desktopLiveSupported, setDesktopLiveSupported] = useState(false);
  const [desktopLoadError, setDesktopLoadError] = useState("");
  const [monitoring, setMonitoring] =
    useState<MonitoringSnapshot | null>(null);

  const [employeeId, setEmployeeId] = useState("");
  const [deviceId, setDeviceId] = useState("");

  const [allowed, setAllowed] = useState(false);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [requesting, setRequesting] = useState(false);
  const [stopping, setStopping] = useState(false);

  const [session, setSession] =
    useState<SessionInfo | null>(null);
  const [sessionStatusError, setSessionStatusError] = useState("");

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [viewPaused, setViewPaused] = useState(false);
  const viewerRef = useRef<HTMLDivElement | null>(null);

  const loadData = useCallback(async (initial = false) => {
    if (!workspaceId) {
      setLoading(false);
      return;
    }

    if (initial) setLoading(true);
    else setRefreshing(true);

    setError("");

    try {
      // Authorization is checked by the backend.
      const access =
        await monitoringControlService.liveAccess(workspaceId);

      setAllowed(access.allowed);

      if (!access.allowed) {
        setEmployees([]);
        setDevices([]);
        setMonitoring(null);
        return;
      }

      const results = await Promise.allSettled([
        employeesService.list(workspaceId),
        deviceManagementService.listDevices(workspaceId),
        monitoringService.liveWall(workspaceId),
        (async (): Promise<DesktopAgentDevice[]> => {
          const all: DesktopAgentDevice[] = [];
          for (let offset = 0; offset < 10000; offset += 500) {
            const page = await api.get<DesktopAgentList>(
              `/workspaces/${workspaceId}/desktop-agent/devices?limit=500&offset=${offset}`,
            );
            all.push(...(page.items ?? []));
            if (all.length >= page.total || !page.items?.length) break;
          }
          return all;
        })(),
        api.get<DesktopAgentCapabilities>(
          `/workspaces/${workspaceId}/desktop-agent/capabilities`,
        ),
      ]);

      const employeeResult = results[0];
      const deviceResult = results[1];
      const monitoringResult = results[2];
      const desktopResult = results[3];
      const capabilitiesResult = results[4];
      const notices: string[] = [];

      if (desktopResult.status === "fulfilled") {
        setDesktopAgents(desktopResult.value);
        setDesktopLoadError("");
      } else {
        setDesktopAgents([]);
        setDesktopLoadError("Desktop enrollment API unavailable: " + messageFromError(desktopResult.reason));
      }
      setDesktopLiveSupported(
        capabilitiesResult.status === "fulfilled" && capabilitiesResult.value.live_screen === true,
      );

      let workspaceEmployees: Employee[] = [];
      if (employeeResult.status === "fulfilled") {
        workspaceEmployees = Array.isArray(employeeResult.value.employees)
          ? employeeResult.value.employees
          : [];
      } else {
        notices.push(
          "Employee directory unavailable: " + messageFromError(employeeResult.reason),
        );
      }

      // Fallback only to another authenticated, workspace-scoped API.
      // Its monitoring.all/team/self permission checks remain enforced server-side.
      // Never manufacture employees from unscoped device records.
      if (workspaceEmployees.length === 0) {
        try {
          const scoped = await monitoringService.employees(workspaceId);
          const scopedRows = Array.isArray(scoped.items) ? scoped.items : [];
          workspaceEmployees = scopedRows.flatMap((row): Employee[] => {
            const id = typeof row.employee_id === "string"
              ? row.employee_id
              : typeof row.id === "string" ? row.id : "";
            const name = typeof row.name === "string"
              ? row.name
              : typeof row.employee === "string" ? row.employee : "";
            if (!id || !name) return [];
            // This normalized view is used only by the employee selector.
            return [{ id, full_name: name } as Employee];
          });
          if (workspaceEmployees.length > 0) {
            notices.length = 0;
          } else {
            notices.push("No employees returned by the authorized workspace APIs.");
          }
        } catch (cause) {
          notices.push(
            "Monitoring employee list unavailable: " + messageFromError(cause),
          );
        }
      }
      setEmployees(workspaceEmployees);

      if (deviceResult.status === "fulfilled") {
        const rows = deviceResult.value.devices;
        setDevices(Array.isArray(rows) ? rows : []);
        if (!Array.isArray(rows) || rows.length === 0) {
          notices.push("No registered devices returned by Device Management.");
        }
      } else {
        setDevices([]);
        notices.push(
          "Device Management unavailable: " + messageFromError(deviceResult.reason),
        );
      }

      if (monitoringResult.status === "fulfilled") {
        setMonitoring(monitoringResult.value);
      } else {
        setMonitoring(null);
        notices.push(
          "Monitoring summary unavailable: " + messageFromError(monitoringResult.reason),
        );
      }

      if (notices.length > 0) {
        setError(notices.join(" "));
      }
    } catch (cause) {
      setAllowed(false);
      setError(messageFromError(cause));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [workspaceId]);

  useEffect(() => {
    setEmployeeId("");
    setDeviceId("");
    setDesktopDeviceId("");
    setSession(null);
    setSessionStatusError("");
    setAllowed(false);
    void loadData(true);
  }, [loadData]);

  // The API reports authorization/session state, NOT actual decoded video.
  // Avoid displaying a fake LIVE badge until a media transport is attached.
  useEffect(() => {
    if (!workspaceId || !session?.sessionId || !allowed) return;
    let cancelled = false;
    let inFlight = false;
    const poll = async () => {
      if (inFlight || cancelled) return;
      inFlight = true;
      try {
        const latest = await monitoringService.getLiveSession(workspaceId, session.sessionId);
        if (cancelled) return;
        setSessionStatusError("");
        setSession((existing) => existing?.sessionId === latest.id
          ? { ...existing, status: latest.status }
          : existing);
      } catch (cause) {
        if (!cancelled) setSessionStatusError(messageFromError(cause));
      } finally {
        inFlight = false;
      }
    };
    void poll();
    const timer = window.setInterval(() => void poll(), 5000);
    return () => { cancelled = true; window.clearInterval(timer); };
  }, [workspaceId, session?.sessionId, allowed]);

  const sessionEnded = session !== null && [
    "ended", "expired", "denied", "rejected", "cancelled", "failed",
  ].includes(session.status.toLowerCase());

  const selectedEmployee = useMemo(
    () => employees.find((item) => item.id === employeeId),
    [employees, employeeId],
  );

  const employeeDevices = useMemo(
    () => devices.filter(
      (device) =>
        Boolean(employeeId) &&
        device.employee_id === employeeId,
    ),
    [devices, employeeId],
  );

  const selectedDevice = useMemo(
    () => employeeDevices.find(
      (device) => device.id === deviceId,
    ),
    [employeeDevices, deviceId],
  );

  const selectedDesktopAgent = desktopAgents.find(
    (item) => item.id === desktopDeviceId && item.employee_id === employeeId,
  );
  const employeeDesktopAgents = desktopAgents.filter(
    (item) => Boolean(employeeId) && item.employee_id === employeeId,
  );
  // Employee selection automatically resolves to an assigned enrolled device.
  // Preserve manual device choice when it still belongs to this employee.
  useEffect(() => {
    if (!employeeId) {
      setDesktopDeviceId("");
      setDeviceId("");
      return;
    }
    const agents = desktopAgents.filter((d) => d.employee_id === employeeId && !d.is_disabled);
    const preferredAgent = agents.find(isDesktopOnline) || agents[0];
    if (!agents.some((d) => d.id === desktopDeviceId)) {
      setDesktopDeviceId(preferredAgent?.id || "");
    }
    const assigned = devices.filter((d) => d.employee_id === employeeId);
    const matching = assigned.find((d) => d.hostname.toLowerCase() === preferredAgent?.device_name.toLowerCase());
    const next = matching || assigned.find(isOnline) || assigned[0];
    if (!assigned.some((d) => d.id === deviceId)) {
      setDeviceId(next?.id || "");
    }
  }, [employeeId, desktopAgents, devices, desktopDeviceId, deviceId]);

  // A development relay is not an authenticated workspace media transport.
  const authorizedSessionActive = session?.status.toLowerCase() === "active";
  const streamDeviceName = selectedDesktopAgent?.device_name || "";
  const onlineDevices = devices.filter(isOnline);
  const monitoredCount = Array.isArray(monitoring?.items)
    ? monitoring.items.length
    : 0;

  const canRequest = Boolean(
    workspaceId &&
    allowed &&
    selectedEmployee &&
    selectedDesktopAgent &&
    isDesktopOnline(selectedDesktopAgent) &&
    desktopLiveSupported &&
    !requesting &&
     (!session || sessionEnded),
  );

  async function requestSession() {
    if (
      !workspaceId ||
      !selectedEmployee ||
      !selectedDesktopAgent ||
      !canRequest
    ) {
      return;
    }

    setRequesting(true);
    setError("");
    setSuccess("");

    try {
      const response =
        await monitoringService.requestLiveSession(
          workspaceId,
          selectedDesktopAgent.id,
        );

      if (!response.session_id) {
        throw new Error(
          "The backend did not return a live-session ID.",
        );
      }

      setSession({
        sessionId: response.session_id,
        employeeId: selectedEmployee.id,
        deviceId: selectedDesktopAgent.id,
        status: response.status,
      });
      setSessionStatusError("");

      setSuccess(
        "Live screen session requested. The employee must " +
        "approve sharing before video can begin.",
      );
    } catch (cause) {
      setError(messageFromError(cause));
    } finally {
      setRequesting(false);
    }
  }

  async function endSession() {
    if (!workspaceId || !session || stopping || sessionEnded) return;

    setStopping(true);
    setError("");

    try {
      await monitoringService.stopLiveSession(
        workspaceId,
        session.sessionId,
      );

      setSession(null);
      setSuccess("The live-session request was ended.");
    } catch (cause) {
      setError(messageFromError(cause));
    } finally {
      setStopping(false);
    }
  }

  return (
    <WorkspaceRequired>
      <main className="ls-page">
        <header className="ls-header">
          <div>
            <div className="ls-crumb">Workspace <span>/</span> Monitoring <span>/</span> <b>Live Screen</b></div>
            <h1>Live Screen</h1>
            <p>View an authorized live screen session of an employee&apos;s assigned device in real time.</p>
          </div>
          <button type="button" className="ls-refresh" onClick={() => void loadData()} disabled={refreshing}>
            <RefreshCw size={16} className={refreshing ? "ls-rotate" : ""} /> Refresh
          </button>
        </header>

        {error && <div className="ls-error" role="alert"><AlertCircle size={18}/>{error}</div>}
        {sessionStatusError && <div className="ls-error" role="alert"><AlertCircle size={18}/> Session status unavailable: {sessionStatusError}</div>}
        {success && <div className="ls-notice" role="status"><CheckCircle2 size={18}/>{success}</div>}

        {loading ? <div className="ls-empty">Loading authorized employees and devices...</div> : !allowed ? (
          <div className="ls-empty"><ShieldCheck size={28}/><strong>Live Screen access restricted</strong><p>Your workspace role is not authorized to view this page.</p></div>
        ) : <>
          <section className="ls-picker">
            <div className="ls-field">
              <label htmlFor="ls-employee"><Users size={17}/> Employee</label>
              <select id="ls-employee" value={employeeId} disabled={Boolean(session && !sessionEnded)} onChange={(e) => {
                setEmployeeId(e.target.value); setDesktopDeviceId(""); setDeviceId(""); setViewPaused(false); setSuccess("");
              }}>
                <option value="">Select employee</option>
                {employees.map((person) => <option key={person.id} value={person.id}>{person.full_name || `${person.first_name || ""} ${person.last_name || ""}`.trim()}</option>)}
              </select>
            </div>
            <div className="ls-field">
              <label htmlFor="ls-device"><Laptop2 size={17}/> Assigned device</label>
              <select id="ls-device" value={desktopDeviceId} disabled={!employeeId || Boolean(session && !sessionEnded)} onChange={(e) => {
                const value = e.target.value;
                setDesktopDeviceId(value);
                const agent = desktopAgents.find((d) => d.id === value);
                const registered = employeeDevices.find((d) => d.hostname.toLowerCase() === agent?.device_name.toLowerCase());
                setDeviceId(registered?.id || ""); setViewPaused(false);
              }}>
                <option value="">{employeeId ? "No enrolled device selected" : "Select an employee first"}</option>
                {employeeDesktopAgents.map((d) => <option key={d.id} value={d.id}>{d.device_name} · {isDesktopOnline(d) ? "Online" : "Offline"}</option>)}
              </select>
            </div>
            <div className="ls-availability"><span>Status</span><strong className={selectedDesktopAgent && isDesktopOnline(selectedDesktopAgent) ? "ls-ready" : "ls-wait"}>
              <span className="ls-dot"/>{selectedDesktopAgent ? isDesktopOnline(selectedDesktopAgent) ? "Agent online" : "Agent offline" : "Not selected"}
            </strong></div>
            <button type="button" className="ls-request" disabled={!canRequest} onClick={() => void requestSession()}>
              <Play size={17}/>{requesting ? "Requesting..." : "Request session"}
            </button>
          </section>

          <div className="ls-columns">
            <section className="ls-panel">
              <div className="ls-consent"><ShieldCheck size={23}/><div>
                <strong>Session shared with employee awareness</strong>
                <span>Viewing is available only for an authorized, active sharing session. The employee can stop sharing.</span>
              </div></div>
              <div className="ls-toolbar">
                <div className="ls-streamlabel"><span className="ls-dot"/>
                  <strong>{selectedDesktopAgent ? `Viewer · ${selectedDesktopAgent.device_name}` : "Select an employee to view their screen"}</strong>
                </div>
                <div className="ls-actions">
                  <button type="button" disabled={!streamDeviceName} onClick={() => setViewPaused((v) => !v)}>
                    {viewPaused ? <Play size={15}/> : <Pause size={15}/>}{viewPaused ? "Resume viewer" : "Pause viewer"}
                  </button>
                  <button type="button" title="Fullscreen" onClick={() => void viewerRef.current?.requestFullscreen?.()}><Maximize2 size={16}/> Fit screen</button>
                  {session && !sessionEnded && <button type="button" className="ls-end" disabled={stopping} onClick={() => void endSession()}><Square size={14}/>{stopping ? "Ending..." : "End request"}</button>}
                </div>
              </div>
              <div className="ls-screen" ref={viewerRef}>
                <div className="ls-screenempty" role="status" aria-live="polite">
                  <MonitorPlay size={48}/>
                  <h3>{viewPaused ? "Viewer paused" : !selectedDesktopAgent ? "Select an employee" : !isDesktopOnline(selectedDesktopAgent) ? "Agent offline or heartbeat stale" : !desktopLiveSupported ? "Live screen unavailable" : !session ? "Request employee sharing" : sessionEnded ? "Session ended" : !authorizedSessionActive ? "Waiting for employee authorization" : "Awaiting secure media transport"}</h3>
                  <p>{viewPaused ? "Resume the viewer when you are ready." : !selectedDesktopAgent ? "Choose an employee to resolve their assigned device." : !isDesktopOnline(selectedDesktopAgent) ? "Check the agent heartbeat and device connection." : !desktopLiveSupported ? "The backend does not advertise desktop live streaming. No development token is needed here." : !session ? "Request a session. Sharing requires an authorized employee decision." : sessionEnded ? "Request a new session if sharing is still required." : !authorizedSessionActive ? "The employee must approve the request before viewing." : "The session is active, but the production viewer media transport has not been implemented. No screen frames are being received."}</p>
                </div>
              </div>
              <div className="ls-foot"><span><ShieldCheck size={15}/> Permission-controlled viewing</span><span><Eye size={15}/> Production media transport pending</span></div>
              {!desktopLiveSupported && <p className="ls-note">Desktop-agent live capability is not advertised by the current backend. A local development relay does not provide production authorization or backend readiness.</p>}
            </section>

            <aside className="ls-details"><h2>Session details <ShieldCheck size={16}/></h2>
              <div className="ls-detail"><Users/><span>Employee<strong>{selectedEmployee?.full_name || "Not selected"}</strong></span></div>
              <div className="ls-detail"><Laptop2/><span>Device<strong>{streamDeviceName || "Not selected"}</strong></span></div>
              <div className="ls-detail"><ShieldCheck/><span>Viewing permission<strong className="ls-green">Active employee authorization required</strong></span></div>
              <div className="ls-detail"><Settings2/><span>Device status<strong>{selectedDesktopAgent ? isDesktopOnline(selectedDesktopAgent) ? "Agent online" : "Agent offline / stale" : "Not selected"}</strong></span></div>
              <div className="ls-detail"><Clock3/><span>Last agent signal<strong>{formatDate(selectedDesktopAgent?.last_seen_at || null)}</strong></span></div>
              <div className="ls-detail"><Activity/><span>Backend session<strong>{session?.status || "No session requested"}</strong></span></div>
              <div className="ls-detail"><Wifi/><span>Transport<strong>Not configured</strong></span></div>
            </aside>
          </div>

          <section className="ls-other"><div className="ls-otherhead"><h2><Monitor size={20}/> Other devices for {selectedEmployee?.full_name || "selected employee"}</h2><span>{employeeDevices.length} registered</span></div>
            <div className="ls-devicegrid">{employeeDevices.map((d) => <button key={d.id} type="button" className={`ls-devicecard ${deviceId === d.id ? "selected" : ""}`} disabled={Boolean(session && !sessionEnded)} onClick={() => {
              setEmployeeId(d.employee_id || ""); setDeviceId(d.id);
              const agent = desktopAgents.find((a) => a.employee_id === d.employee_id && a.device_name.toLowerCase() === d.hostname.toLowerCase());
              setDesktopDeviceId(agent?.id || ""); setViewPaused(false);
            }}><Laptop2 size={29}/><span><strong>{d.hostname}</strong><small>{d.os_name} {d.os_version || ""}</small></span><em className={isOnline(d) ? "online" : "offline"}>{isOnline(d) ? "Online" : "Offline"}</em></button>)}
            {!employeeDevices.length && <p className="ls-deviceempty">No assigned devices for the selected employee.</p>}</div>
          </section>
        </>}
        <style jsx>{`
          .ls-page{--ink:#152137;--line:#e7e4df;--muted:#778397;min-height:100%;padding:22px 20px 34px;background:#faf9f7;color:var(--ink);font-size:13px}
          .ls-page *{box-sizing:border-box}.ls-header{display:flex;align-items:center;justify-content:space-between;gap:20px;margin-bottom:19px}
          .ls-crumb{font-size:12px;color:#778397;margin-bottom:17px}.ls-crumb span{margin:0 10px;color:#aeb6c0}.ls-crumb b{color:var(--ink)}
          .ls-header h1{font-size:29px;line-height:1.2;letter-spacing:-.7px;margin:0;font-weight:760}.ls-header p{font-size:14px;margin:5px 0 0;color:#78859a}
          button,select{font:inherit}.ls-refresh,.ls-actions button{display:inline-flex;align-items:center;justify-content:center;gap:8px;border:1px solid #dfe3e8;border-radius:7px;background:white;color:var(--ink);padding:10px 12px;cursor:pointer;white-space:nowrap}
          button:disabled{opacity:.48;cursor:not-allowed}.ls-picker{display:grid;grid-template-columns:minmax(190px,1.35fr) minmax(190px,1fr) 132px auto;align-items:end;gap:18px;background:#fffdfa;border:1px solid #ece5da;border-radius:12px;padding:16px 17px;margin-bottom:16px}
          .ls-field{display:grid;gap:8px;min-width:0}.ls-field label{display:flex;gap:9px;align-items:center;font-weight:700}.ls-field select{width:100%;border:1px solid #e0e3e8;border-radius:8px;background:#fff;height:40px;padding:0 11px;color:var(--ink)}
          .ls-availability{display:grid;gap:9px}.ls-availability>span{font-weight:700}.ls-availability strong{min-height:40px;display:flex;align-items:center;gap:9px;border-radius:8px;padding:0 9px;font-weight:650}.ls-ready{background:#e8f7ed;color:#157c43}.ls-wait{background:#f1f2f4;color:#606d7c}
          .ls-dot{display:inline-block;flex-shrink:0;width:10px;height:10px;background:#18aa63;border-radius:50%}.ls-wait .ls-dot{background:#9fa9b6}
          .ls-request{height:40px;display:inline-flex;align-items:center;justify-content:center;gap:10px;background:#101923;color:white;border:1px solid #101923;border-radius:7px;padding:0 16px;font-weight:700;white-space:nowrap;cursor:pointer}
          .ls-columns{display:grid;grid-template-columns:minmax(0,1fr) 265px;gap:16px;align-items:stretch}.ls-panel,.ls-details,.ls-other{border-radius:12px;border:1px solid var(--line);background:#fffdfa;overflow:hidden}
          .ls-consent{display:flex;align-items:flex-start;gap:15px;padding:15px;background:#e4f8ed;color:#08733d;border-bottom:1px solid #c6edd6}.ls-consent>div{display:grid;gap:4px}.ls-consent strong{font-size:13px}.ls-consent span{font-size:12px;color:#426a56}
          .ls-toolbar{min-height:55px;padding:9px 13px;display:flex;align-items:center;justify-content:space-between;gap:12px}.ls-streamlabel,.ls-actions{display:flex;align-items:center;gap:11px}.ls-streamlabel strong{font-size:13px}.ls-actions{gap:7px}.ls-actions button{font-size:12px;padding:8px 10px}.ls-actions .ls-end{color:#cf2f27;border-color:#f8aba4}
          .ls-screen{background:#111;min-height:425px;position:relative;display:grid;place-items:center;overflow:hidden}.ls-screen:fullscreen{background:black}.ls-screen :global(img){max-width:100%;max-height:75vh;object-fit:contain}.ls-screenempty{text-align:center;max-width:360px;color:#b9c0c9;padding:30px}.ls-screenempty h3{color:white;margin:15px 0 8px}.ls-screenempty p{line-height:1.6}
          .ls-foot{display:flex;justify-content:space-between;gap:14px;padding:13px 15px;color:#7f8ca1;font-size:12px}.ls-foot span{display:flex;gap:7px;align-items:center}.ls-note{color:#8d6e30;font-size:11px;padding:0 15px 10px;line-height:1.5}
          .ls-details h2{font-size:15px;margin:0;padding:17px;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between}.ls-detail{display:flex;align-items:flex-start;gap:12px;padding:14px 16px}.ls-detail :global(svg){width:19px;height:19px;flex:none;margin-top:2px}.ls-detail span{display:grid;gap:5px;color:#78869b;font-size:12px}.ls-detail strong{color:#17243b;font-size:13px;overflow-wrap:anywhere}.ls-detail .ls-green{color:#14824b}
          .ls-other{margin-top:15px;padding:17px}.ls-otherhead{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px}.ls-otherhead h2{display:flex;align-items:center;gap:9px;font-size:16px;margin:0}.ls-otherhead span{color:var(--muted);font-size:12px}.ls-devicegrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:11px}.ls-devicecard{display:flex;align-items:center;gap:12px;min-width:0;background:white;border:1px solid #e5e6e9;border-radius:8px;padding:14px;cursor:pointer;text-align:left}.ls-devicecard.selected{border-color:#efb322;background:#fffaf0}.ls-devicecard span{min-width:0;flex:1;display:grid;gap:5px}.ls-devicecard strong{font-size:12px;overflow-wrap:anywhere}.ls-devicecard small{font-size:11px;color:var(--muted)}.ls-devicecard em{font-size:10px;padding:5px 9px;border-radius:25px;font-style:normal}.ls-devicecard em.online{background:#e1f5e9;color:#147e46}.ls-devicecard em.offline{background:#fde8e8;color:#b64141}.ls-deviceempty{color:var(--muted)}
          .ls-error,.ls-notice{display:flex;gap:10px;align-items:center;padding:11px 14px;margin:10px 0;border-radius:8px}.ls-error{background:#fff0ef;color:#a62521}.ls-notice{background:#e4f8ed;color:#11753f}.ls-empty{min-height:230px;display:grid;align-content:center;justify-items:center;gap:12px;text-align:center}
          @keyframes spin{to{transform:rotate(360deg)}}.ls-rotate{animation:spin 1s linear infinite}
          @media(max-width:1250px){.ls-picker{grid-template-columns:1fr 1fr}.ls-columns{grid-template-columns:minmax(0,1fr) 250px}.ls-toolbar{flex-wrap:wrap}}
          @media(max-width:900px){.ls-columns{grid-template-columns:1fr}.ls-details{display:grid;grid-template-columns:1fr 1fr}.ls-details h2{grid-column:1/-1}}
          @media(max-width:600px){.ls-page{padding:14px}.ls-picker{grid-template-columns:1fr}.ls-header{align-items:flex-start}.ls-header h1{font-size:24px}.ls-header p{font-size:12px}.ls-details{grid-template-columns:1fr}.ls-toolbar{align-items:flex-start}.ls-actions{flex-wrap:wrap}.ls-screen{min-height:280px}.ls-foot{flex-direction:column}}
        `}</style>
      </main>
    </WorkspaceRequired>
  );
}
