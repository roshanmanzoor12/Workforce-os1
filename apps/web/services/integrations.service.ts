import { api } from "@/lib/api/client";

import type {
  AnalyticsOverviewResponse,
} from "@/types/integration-analytics";

import type {
  APIKeyCreateRequest,
  APIKeyCreateResponse,
  APIKeyPublic,
  APIKeyRotateResponse,
} from "@/types/api-keys";

export interface IntegrationReportDefinition {
  key:
    | "attendance"
    | "payroll"
    | "productivity"
    | "device_health"
    | "monitoring_summary"
    | "goals"
    | "audit";

  label: string;
  description: string;

  supported_scopes: (
    | "self"
    | "team"
    | "workspace"
  )[];

  supported_formats: (
    | "json"
    | "csv"
  )[];

  supports_time_range: boolean;
  supports_employee_filter: boolean;
  supports_team_filter: boolean;
  supports_department_filter: boolean;
  supports_status_filter: boolean;
}

export interface IntegrationReportCatalogResponse {
  items: IntegrationReportDefinition[];
}

export interface IntegrationReportRunRequest {
  report: IntegrationReportDefinition["key"];

  scope:
    | "self"
    | "team"
    | "workspace";

  start_at?: string | null;
  end_at?: string | null;
  employee_id?: string | null;
  team_id?: string | null;
  department_id?: string | null;
  status?: string | null;
  limit?: number;
}

export interface IntegrationReportRunResponse {
  workspace_id: string;

  report:
    | "attendance"
    | "payroll"
    | "productivity"
    | "device_health"
    | "monitoring_summary"
    | "goals"
    | "audit";

  scope:
    | "self"
    | "team"
    | "workspace";

  generated_at: string;

  parameters: {
    start_at: string | null;
    end_at: string | null;
    employee_id: string | null;
    team_id: string | null;
    department_id: string | null;
    status: string | null;
    limit: number;
  };

  data: Record<
    string,
    unknown
  >;
}

export const integrationsService = {
  listApiKeys(
    workspaceId: string,
    limit = 100,
    offset = 0,
  ) {
    return api.get<
      APIKeyPublic[]
    >(
      `/workspaces/${workspaceId}/api-keys`,
      {
        query: {
          limit,
          offset,
        },
      },
    );
  },

  createApiKey(
    workspaceId: string,
    payload: APIKeyCreateRequest,
  ) {
    return api.post<APIKeyCreateResponse>(
      `/workspaces/${workspaceId}/api-keys`,
      payload,
    );
  },

  getApiKey(
    workspaceId: string,
    keyId: string,
  ) {
    return api.get<APIKeyPublic>(
      `/workspaces/${workspaceId}/api-keys/${keyId}`,
    );
  },

  revokeApiKey(
    workspaceId: string,
    keyId: string,
  ) {
    return api.post<APIKeyPublic>(
      `/workspaces/${workspaceId}/api-keys/${keyId}/revoke`,
      {},
    );
  },

  rotateApiKey(
    workspaceId: string,
    keyId: string,
  ) {
    return api.post<APIKeyRotateResponse>(
      `/workspaces/${workspaceId}/api-keys/${keyId}/rotate`,
      {},
    );
  },

  reportCatalog(
    workspaceId: string,
  ) {
    return api.get<
      IntegrationReportCatalogResponse
    >(
      `/workspaces/${workspaceId}/integrations/reports/catalog`,
    );
  },

  runReport(
    workspaceId: string,
    payload: IntegrationReportRunRequest,
  ) {
    return api.post<
      IntegrationReportRunResponse
    >(
      `/workspaces/${workspaceId}/integrations/reports/run`,
      payload,
    );
  },

  analyticsOverview(
    workspaceId: string,
    startAt?: string,
    endAt?: string,
  ) {
    return api.get<
      AnalyticsOverviewResponse
    >(
      `/workspaces/${workspaceId}/integrations/analytics/overview`,
      {
        query: {
          start_at:
            startAt || undefined,
          end_at:
            endAt || undefined,
        },
      },
    );
  },
};