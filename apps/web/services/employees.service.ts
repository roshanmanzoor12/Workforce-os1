import {
  api,
} from "@/lib/api/client";


export type EmploymentStatus =
  | "active"
  | "on_leave"
  | "suspended"
  | "terminated";


export interface Employee {
  id: string;

  user_id:
    string | null;

  employee_code:
    string;

  first_name:
    string;

  last_name:
    string;

  full_name:
    string;

  work_email:
    string | null;

  phone_number:
    string | null;

  avatar_url:
    string | null;

  job_title:
    string | null;

  employment_status:
    EmploymentStatus;

  hire_date:
    string | null;

  termination_date:
    string | null;

  department_id:
    string | null;

  team_id:
    string | null;

  manager_id:
    string | null;

  is_active:
    boolean;

  created_at:
    string;

  updated_at:
    string;
}


export interface EmployeeListResponse {
  employees:
    Employee[];

  total:
    number;
}


export interface EmployeeResponse {
  message:
    string;

  employee:
    Employee;
}


export interface EmployeeCreatePayload {
  user_id?:
    string | null;

  employee_code:
    string;

  first_name:
    string;

  last_name:
    string;

  work_email?:
    string | null;

  phone_number?:
    string | null;

  avatar_url?:
    string | null;

  job_title?:
    string | null;

  employment_status?:
    EmploymentStatus;

  hire_date?:
    string | null;

  termination_date?:
    string | null;

  department_id?:
    string | null;

  team_id?:
    string | null;

  manager_id?:
    string | null;
}


export interface EmployeeUpdatePayload {
  user_id?:
    string | null;

  employee_code?:
    string | null;

  first_name?:
    string | null;

  last_name?:
    string | null;

  work_email?:
    string | null;

  phone_number?:
    string | null;

  avatar_url?:
    string | null;

  job_title?:
    string | null;

  employment_status?:
    EmploymentStatus | null;

  hire_date?:
    string | null;

  termination_date?:
    string | null;

  department_id?:
    string | null;

  team_id?:
    string | null;

  manager_id?:
    string | null;

  is_active?:
    boolean | null;
}


async function list(
  workspaceId:
    string,

  filters?: {
    departmentId?:
      string | null;

    teamId?:
      string | null;

    managerId?:
      string | null;

    employmentStatus?:
      EmploymentStatus | null;

    includeInactive?:
      boolean;

    search?:
      string | null;
  },
): Promise<EmployeeListResponse> {
  return api.get<EmployeeListResponse>(
    `/workspaces/${workspaceId}/employees`,
    {
      query: {
        department_id:
          filters?.departmentId,

        team_id:
          filters?.teamId,

        manager_id:
          filters?.managerId,

        employment_status:
          filters?.employmentStatus,

        include_inactive:
          filters?.includeInactive ??
          false,

        search:
          filters?.search,
      },
    },
  );
}


async function create(
  workspaceId:
    string,

  payload:
    EmployeeCreatePayload,
): Promise<EmployeeResponse> {
  return api.post<EmployeeResponse>(
    `/workspaces/${workspaceId}/employees`,
    payload,
  );
}


async function update(
  workspaceId:
    string,

  employeeId:
    string,

  payload:
    EmployeeUpdatePayload,
): Promise<EmployeeResponse> {
  return api.patch<EmployeeResponse>(
    `/workspaces/${workspaceId}/employees/${employeeId}`,
    payload,
  );
}


async function deactivate(
  workspaceId:
    string,

  employeeId:
    string,
): Promise<{
  message:
    string;

  success:
    boolean;
}> {
  return api.delete<{
    message:
      string;

    success:
      boolean;
  }>(
    `/workspaces/${workspaceId}/employees/${employeeId}`,
  );
}


export const employeesService = {
  list,
  create,
  update,
  deactivate,
};