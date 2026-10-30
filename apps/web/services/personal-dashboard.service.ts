import { api } from "@/lib/api/client";

export interface PersonalDashboardResponse {
  generated_at: string;
  friends_total: number | null;
  online_total: number | null;
  incoming_requests: number | null;
  conversations_total: number | null;
  calls_total: number | null;
  friends: { user_id: string; name: string; online: boolean }[];
  conversations: { id: string; name: string; kind: string; updated_at: string }[];
  calls: { id: string; conversation_id: string; kind: string; status: string; created_at: string }[];
  errors: Record<string, string>;
}

export const personalDashboardService = {
  get: () => api.get<PersonalDashboardResponse>("/personal/dashboard"),
};