import { api } from "@/lib/api/client";

import type {
  CyclePublic,
  ReviewCreate,
  ReviewCycleCreate,
  ReviewList,
  ReviewPublic,
} from "@/types/performance";

async function createCycle(
  workspaceId: string,
  payload: ReviewCycleCreate,
): Promise<CyclePublic> {
  return api.post<CyclePublic>(
    `/workspaces/${workspaceId}/performance/cycles`,
    payload,
  );
}

async function createReview(
  workspaceId: string,
  payload: ReviewCreate,
): Promise<ReviewPublic> {
  return api.post<ReviewPublic>(
    `/workspaces/${workspaceId}/performance/reviews`,
    payload,
  );
}

async function listReviews(
  workspaceId: string,
  employeeId?: string | null,
): Promise<ReviewList> {
  return api.get<ReviewList>(
    `/workspaces/${workspaceId}/performance/reviews`,
    {
      query: {
        employee_id: employeeId ?? undefined,
      },
    },
  );
}

export const performanceService = {
  createCycle,
  createReview,
  listReviews,
};