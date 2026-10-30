import { api } from "@/lib/api/client";

import type {
  IncidentCreate,
  IncidentList,
  IncidentPublic,
  IncidentUpdate,
} from "@/types/discipline";

async function createIncident(
  workspaceId: string,
  payload: IncidentCreate,
): Promise<IncidentPublic> {
  return api.post<IncidentPublic>(
    `/workspaces/${workspaceId}/discipline/incidents`,
    payload,
  );
}

async function listIncidents(
  workspaceId: string,
  employeeId?: string | null,
): Promise<IncidentList> {
  return api.get<IncidentList>(
    `/workspaces/${workspaceId}/discipline/incidents`,
    {
      query: {
        employee_id: employeeId ?? undefined,
      },
    },
  );
}

async function updateIncident(
  workspaceId: string,
  incidentId: string,
  payload: IncidentUpdate,
): Promise<IncidentPublic> {
  return api.patch<IncidentPublic>(
    `/workspaces/${workspaceId}/discipline/incidents/${incidentId}`,
    payload,
  );
}

export const disciplineService = {
  createIncident,
  listIncidents,
  updateIncident,
};