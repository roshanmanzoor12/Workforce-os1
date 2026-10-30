import {
  api,
} from "@/lib/api/client";

import type {
  DeviceActivationCodeCreateRequest,
  DeviceActivationCodeCreateResponse,
  DeviceActivationCodeListResponse,
  DeviceActivationCodeRevokeResponse,
  DeviceAssignmentRequest,
  DeviceDeleteResponse,
  DeviceListResponse,
  DeviceResponse,
  DeviceStatus,
} from "@/types/device-management";


async function listDevices(
  workspaceId:
    string,

  options?: {
    employeeId?:
      string | null;

    status?:
      DeviceStatus | null;

    includeInactive?:
      boolean;

    search?:
      string | null;
  },
): Promise<DeviceListResponse> {
  return api.get<DeviceListResponse>(
    `/workspaces/${workspaceId}/devices`,
    {
      query: {
        employee_id:
          options?.employeeId,

        status:
          options?.status,

        include_inactive:
          options?.includeInactive ??
          false,

        search:
          options?.search,
      },
    },
  );
}


async function assignDevice(
  workspaceId:
    string,

  deviceId:
    string,

  payload:
    DeviceAssignmentRequest,
): Promise<DeviceResponse> {
  return api.patch<DeviceResponse>(
    `/workspaces/${workspaceId}/devices/${deviceId}/assignment`,
    payload,
  );
}


async function revokeDevice(
  workspaceId:
    string,

  deviceId:
    string,
): Promise<DeviceDeleteResponse> {
  return api.delete<DeviceDeleteResponse>(
    `/workspaces/${workspaceId}/devices/${deviceId}`,
  );
}


async function createActivationCode(
  workspaceId:
    string,

  payload:
    DeviceActivationCodeCreateRequest,
): Promise<DeviceActivationCodeCreateResponse> {
  return api.post<DeviceActivationCodeCreateResponse>(
    `/workspaces/${workspaceId}/device-activation-codes`,
    payload,
  );
}


async function listActivationCodes(
  workspaceId:
    string,

  includeInactive =
    false,
): Promise<DeviceActivationCodeListResponse> {
  return api.get<DeviceActivationCodeListResponse>(
    `/workspaces/${workspaceId}/device-activation-codes`,
    {
      query: {
        include_inactive:
          includeInactive,
      },
    },
  );
}


async function revokeActivationCode(
  workspaceId:
    string,

  activationId:
    string,
): Promise<DeviceActivationCodeRevokeResponse> {
  return api.delete<DeviceActivationCodeRevokeResponse>(
    `/workspaces/${workspaceId}/device-activation-codes/${activationId}`,
  );
}


export const deviceManagementService = {
  listDevices,

  assignDevice,

  revokeDevice,

  createActivationCode,

  listActivationCodes,

  revokeActivationCode,
};