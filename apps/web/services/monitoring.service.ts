import { api } from "@/lib/api/client";

export type MonitoringStatus = "online" | "idle" | "offline" | "unavailable";

export interface MonitoringSnapshot {
  summary?: Record<string, number | string>;
  items?: Array<Record<string, unknown>>;
  total?: number;
  generated_at?: string;
  [key: string]: unknown;
}

const path = (workspaceId: string, section: string) =>
  `/workspaces/${workspaceId}/monitoring/${section}`;

export const monitoringService = {
  overview(workspaceId: string) { return api.get<MonitoringSnapshot>(path(workspaceId, "overview")); },
  employees(workspaceId: string, query = "") { return api.get<MonitoringSnapshot>(`${path(workspaceId, "employees")}${query}`); },
  devices(workspaceId: string, query = "") { return api.get<MonitoringSnapshot>(`${path(workspaceId, "devices")}${query}`); },
  liveWall(workspaceId: string, query = "") { return api.get<MonitoringSnapshot>(`${path(workspaceId, "live-wall")}${query}`); },
  screenshots(workspaceId: string, query = "") { return api.get<MonitoringSnapshot>(`${path(workspaceId, "screenshots")}${query}`); },
  activity(workspaceId: string, query = "") { return api.get<MonitoringSnapshot>(`${path(workspaceId, "activity")}${query}`); },
  applications(workspaceId: string, query = "") { return api.get<MonitoringSnapshot>(`${path(workspaceId, "applications")}${query}`); },
  websites(workspaceId: string, query = "") { return api.get<MonitoringSnapshot>(`${path(workspaceId, "websites")}${query}`); },
  attendance(workspaceId: string, query = "") { return api.get<MonitoringSnapshot>(`${path(workspaceId, "attendance")}${query}`); },
  alerts(workspaceId: string, query = "") { return api.get<MonitoringSnapshot>(`${path(workspaceId, "alerts")}${query}`); },
  reports(workspaceId: string, query = "") { return api.get<MonitoringSnapshot>(`${path(workspaceId, "reports")}${query}`); },
  // Match the real FastAPI live_monitoring router rather than /monitoring/*.
  requestLiveSession(workspaceId: string, deviceId: string) {
    return api.post<{ id: string; device_id: string; employee_id: string; status: string }>(
      `/workspaces/${workspaceId}/live-monitoring/live-sessions`,
      { device_id: deviceId },
    ).then((result) => ({ ...result, session_id: result.id }));
  },
  getLiveSession(workspaceId: string, sessionId: string) {
    return api.get<{ id: string; device_id: string; employee_id: string; status: string; session_channel: string | null }>(
      `/workspaces/${workspaceId}/live-monitoring/live-sessions/${sessionId}`,
    );
  },
  stopLiveSession(workspaceId: string, sessionId: string) {
    return api.post(
      `/workspaces/${workspaceId}/live-monitoring/live-sessions/${sessionId}/end`,
      { reason: "Stopped by authorized viewer" },
    );
  },
  saveScreenConsent(workspaceId: string, granted: boolean) {
    return api.post(path(workspaceId, "consent"), { granted, source: "native_agent" });
  },
};

