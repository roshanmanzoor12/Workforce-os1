import {
  api,
} from "@/lib/api/client";

import type {
  AttendanceEventCreateRequest,
  AttendanceEventResponse,
  AttendanceListResponse,
  AttendanceRecordDetailResponse,
  AttendanceRecordResponse,
  AttendanceRecordUpdateRequest,
  AttendanceStatus,
  AttendanceSummaryResponse,
} from "@/types/attendance";


interface AttendanceListOptions {
  employeeId?:
    string | null;

  startDate?:
    string | null;

  endDate?:
    string | null;

  status?:
    AttendanceStatus | null;
}


async function list(
  workspaceId:
    string,

  options?:
    AttendanceListOptions,
): Promise<AttendanceListResponse> {
  const response =
    await api.get<AttendanceListResponse>(
      `/workspaces/${workspaceId}/attendance/records`,
      {
        query: {
          employee_id:
            options?.employeeId ??
            undefined,

          start_date:
            options?.startDate ??
            undefined,

          end_date:
            options?.endDate ??
            undefined,

          status:
            options?.status ??
            undefined,
        },
      },
    );


  return {
    ...response,

    attendance:
      response.attendance ??
      [],
  };
}


async function get(
  workspaceId:
    string,

  attendanceRecordId:
    string,
): Promise<AttendanceRecordDetailResponse> {
  const response =
    await api.get<AttendanceRecordDetailResponse>(
      `/workspaces/${workspaceId}/attendance/records/${attendanceRecordId}`,
    );


  return {
    ...response,

    events:
      response.events ??
      [],
  };
}


async function update(
  workspaceId:
    string,

  attendanceRecordId:
    string,

  payload:
    AttendanceRecordUpdateRequest,
): Promise<AttendanceRecordResponse> {
  return api.patch<AttendanceRecordResponse>(
    `/workspaces/${workspaceId}/attendance/records/${attendanceRecordId}`,
    payload,
  );
}


async function recordEvent(
  workspaceId:
    string,

  employeeId:
    string,

  payload:
    AttendanceEventCreateRequest,
): Promise<AttendanceEventResponse> {
  return api.post<AttendanceEventResponse>(
    `/workspaces/${workspaceId}/attendance/employees/${employeeId}/events`,
    payload,
  );
}


async function summary(
  workspaceId:
    string,

  employeeId:
    string,

  startDate:
    string,

  endDate:
    string,
): Promise<AttendanceSummaryResponse> {
  return api.get<AttendanceSummaryResponse>(
    `/workspaces/${workspaceId}/attendance/employees/${employeeId}/summary`,
    {
      query: {
        start_date:
          startDate,

        end_date:
          endDate,
      },
    },
  );
}


export const attendanceService = {
  list,

  get,

  update,

  recordEvent,

  summary,
};