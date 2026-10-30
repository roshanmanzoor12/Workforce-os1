import {
  api,
} from "@/lib/api/client";


export interface Department {
  id: string;

  name: string;

  code: string | null;

  description: string | null;

  is_active: boolean;

  created_at: string;

  updated_at: string;
}


export interface DepartmentListResponse {
  departments: Department[];

  total: number;
}


export interface DepartmentResponse {
  message: string;

  department: Department;
}


export interface DepartmentCreateRequest {
  name: string;

  code?: string | null;

  description?: string | null;
}


export interface DepartmentUpdateRequest {
  name?: string | null;

  code?: string | null;

  description?: string | null;

  is_active?: boolean | null;
}


export interface DepartmentDeleteResponse {
  message: string;

  success: boolean;
}


async function list(
  workspaceId: string,
  includeInactive = false,
): Promise<DepartmentListResponse> {
  return api.get<DepartmentListResponse>(
    `/workspaces/${workspaceId}/departments`,
    {
      query: {
        include_inactive:
          includeInactive,
      },
    },
  );
}


async function get(
  workspaceId: string,
  departmentId: string,
): Promise<DepartmentResponse> {
  return api.get<DepartmentResponse>(
    `/workspaces/${workspaceId}/departments/${departmentId}`,
  );
}


async function create(
  workspaceId: string,
  payload: DepartmentCreateRequest,
): Promise<DepartmentResponse> {
  return api.post<DepartmentResponse>(
    `/workspaces/${workspaceId}/departments`,
    payload,
  );
}


async function update(
  workspaceId: string,
  departmentId: string,
  payload: DepartmentUpdateRequest,
): Promise<DepartmentResponse> {
  return api.patch<DepartmentResponse>(
    `/workspaces/${workspaceId}/departments/${departmentId}`,
    payload,
  );
}


async function deactivate(
  workspaceId: string,
  departmentId: string,
): Promise<DepartmentDeleteResponse> {
  return api.delete<DepartmentDeleteResponse>(
    `/workspaces/${workspaceId}/departments/${departmentId}`,
  );
}


export const departmentsService = {
  list,
  get,
  create,
  update,
  deactivate,
};