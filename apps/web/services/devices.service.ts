import { api } from "@/lib/api/client";

export type DeviceStatus =
  | "pending"
  | "active"
  | "offline"
  | "disabled"
  | "revoked";

export interface Device {
  id: string;
  device_uuid: string;
  employee_id: string | null;

  hostname: string;

  os_name: string;
  os_version: string | null;

  architecture: string | null;

  agent_version: string | null;
  agent_identifier: string | null;

  status: DeviceStatus;

  is_active: boolean;

  first_seen_at: string | null;
  last_seen_at: string | null;
  registered_at: string | null;
  revoked_at: string | null;

  monitoring_profile_id:
    | string
    | null;

  created_at: string;
  updated_at: string;
}

export interface DeviceListResponse {
  devices: Device[];
  total: number;
}

export interface DeviceDetailResponse {
  device: Device;
}

export interface DeviceResponse {
  message: string;
  device: Device;
}

export const devicesService = {
  list(
    workspaceId: string,
    filters?: {
      employeeId?: string | null;

      status?:
        | DeviceStatus
        | null;

      includeInactive?: boolean;

      search?: string | null;
    },
  ) {
    return api.get<DeviceListResponse>(
      `/workspaces/${workspaceId}/devices`,
      {
        query: {
          employee_id:
            filters?.employeeId,

          status:
            filters?.status,

          include_inactive:
            filters?.includeInactive ??
            false,

          search:
            filters?.search,
        },
      },
    );
  },

  get(
    workspaceId: string,
    deviceId: string,
  ) {
    return api.get<DeviceDetailResponse>(
      `/workspaces/${workspaceId}/devices/${deviceId}`,
    );
  },

  update(
    workspaceId: string,
    deviceId: string,
    payload: {
      hostname?: string | null;

      employee_id?:
        string | null;

      status?:
        | DeviceStatus
        | null;

      is_active?:
        boolean | null;

      monitoring_profile_id?:
        string | null;
    },
  ) {
    return api.patch<DeviceResponse>(
      `/workspaces/${workspaceId}/devices/${deviceId}`,
      payload,
    );
  },

  assign(
    workspaceId: string,
    deviceId: string,
    employeeId: string | null,
  ) {
    return api.patch<DeviceResponse>(
      `/workspaces/${workspaceId}/devices/${deviceId}/assignment`,
      {
        employee_id:
          employeeId,
      },
    );
  },

  revoke(
    workspaceId: string,
    deviceId: string,
  ) {
    return api.delete<{
      message: string;
      success: boolean;
    }>(
      `/workspaces/${workspaceId}/devices/${deviceId}`,
    );
  },
};