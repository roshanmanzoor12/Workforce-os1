import { api } from "@/lib/api/client";

import type {
  GoalCreateRequest,
  GoalListResponse,
  GoalPublic,
  GoalUpdateRequest,
} from "@/types/goals";


type GoalScope = string | null;

type MineGoalCreate = Omit<
  GoalCreateRequest,
  "owner_employee_id"
> & {
  owner_employee_id?: string;
};


function mineRoute(workspaceId: GoalScope): string {
  return workspaceId
    ? `/workspaces/${workspaceId}/goals/me`
    : "/personal/goals";
}


async function listMine(
  workspaceId: GoalScope,
): Promise<GoalListResponse> {
  return api.get<GoalListResponse>(
    mineRoute(workspaceId),
  );
}


async function createMine(
  workspaceId: GoalScope,
  payload: MineGoalCreate,
): Promise<GoalPublic> {
  if (workspaceId) {
    if (!payload.owner_employee_id) {
      throw new Error(
        "An employee record is required for workspace goals.",
      );
    }

    return api.post<GoalPublic>(
      mineRoute(workspaceId),
      payload,
    );
  }

  return api.post<GoalPublic>(
    mineRoute(null),
    {
      title: payload.title,
      description: payload.description,
      priority: payload.priority,
      start_date: payload.start_date,
      due_date: payload.due_date,
    },
  );
}


async function getMine(
  workspaceId: GoalScope,
  goalId: string,
): Promise<GoalPublic> {
  return api.get<GoalPublic>(
    `${mineRoute(workspaceId)}/${goalId}`,
  );
}


async function updateMine(
  workspaceId: GoalScope,
  goalId: string,
  payload: GoalUpdateRequest,
): Promise<GoalPublic> {
  return api.patch<GoalPublic>(
    `${mineRoute(workspaceId)}/${goalId}`,
    payload,
  );
}


async function deleteMine(
  workspaceId: GoalScope,
  goalId: string,
): Promise<void> {
  await api.delete<void>(
    `${mineRoute(workspaceId)}/${goalId}`,
  );
}


async function listEmployee(
  workspaceId: string,
  employeeId: string,
): Promise<GoalListResponse> {
  return api.get<GoalListResponse>(
    `/workspaces/${workspaceId}/goals/employee/${employeeId}`,
  );
}


async function get(
  workspaceId: string,
  goalId: string,
): Promise<GoalPublic> {
  return api.get<GoalPublic>(
    `/workspaces/${workspaceId}/goals/${goalId}`,
  );
}


async function update(
  workspaceId: string,
  goalId: string,
  payload: GoalUpdateRequest,
): Promise<GoalPublic> {
  return api.patch<GoalPublic>(
    `/workspaces/${workspaceId}/goals/${goalId}`,
    payload,
  );
}


async function remove(
  workspaceId: string,
  goalId: string,
): Promise<void> {
  await api.delete<void>(
    `/workspaces/${workspaceId}/goals/${goalId}`,
  );
}


export const goalsService = {
  listMine,
  createMine,
  getMine,
  updateMine,
  deleteMine,
  listEmployee,
  get,
  update,
  remove,
};