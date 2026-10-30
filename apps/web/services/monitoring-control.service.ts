import {
  api,
} from "@/lib/api/client";

import type {
  MonitoringAccessResponse,
  MonitoringControlSummaryResponse,
} from "@/types/monitoring-control";


async function summary(
  workspaceId:
    string,
): Promise<MonitoringControlSummaryResponse> {
  return api.get<MonitoringControlSummaryResponse>(
    `/workspaces/${workspaceId}/monitoring-control`,
  );
}


async function viewAccess(
  workspaceId:
    string,
): Promise<MonitoringAccessResponse> {
  return api.get<MonitoringAccessResponse>(
    `/workspaces/${workspaceId}/monitoring-control/view-access`,
  );
}


async function liveAccess(
  workspaceId:
    string,
): Promise<MonitoringAccessResponse> {
  return api.get<MonitoringAccessResponse>(
    `/workspaces/${workspaceId}/monitoring-control/live-access`,
  );
}


async function manageAccess(
  workspaceId:
    string,
): Promise<MonitoringAccessResponse> {
  return api.get<MonitoringAccessResponse>(
    `/workspaces/${workspaceId}/monitoring-control/manage-access`,
  );
}


async function settingsAccess(
  workspaceId:
    string,
): Promise<MonitoringAccessResponse> {
  return api.get<MonitoringAccessResponse>(
    `/workspaces/${workspaceId}/monitoring-control/settings-access`,
  );
}


export const monitoringControlService = {
  summary,

  viewAccess,

  liveAccess,

  manageAccess,

  settingsAccess,
};