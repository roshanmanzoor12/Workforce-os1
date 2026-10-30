import {
  api,
} from "@/lib/api/client";


export interface Team {
  id:
    string;

  name:
    string;

  code:
    string | null;

  description:
    string | null;

  department_id:
    string | null;

  is_active:
    boolean;

  created_at:
    string;

  updated_at:
    string;
}


export interface TeamListResponse {
  teams:
    Team[];

  total:
    number;
}


export const teamsService = {
  list(
    workspaceId:
      string,

    options?: {
      departmentId?:
        string | null;

      includeInactive?:
        boolean;
    },
  ) {
    return api.get<TeamListResponse>(
      `/workspaces/${workspaceId}/teams`,
      {
        query: {
          department_id:
            options?.departmentId,

          include_inactive:
            options?.includeInactive ??
            false,
        },
      },
    );
  },
};