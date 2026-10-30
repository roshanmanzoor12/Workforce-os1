import { getAuthSession } from "@/lib/auth/session";
import { api } from "@/lib/api/client";
import type { AuthUser } from "@/types/auth";

export interface PersonalAccount {
  user: AuthUser;
  google_avatar_url?: string | null;
  has_password: boolean;
  last_login_at: string | null;
  password_changed_at: string | null;
  identities: { provider: string; email: string | null; connected_at: string; last_authenticated_at: string | null }[];
}

export interface ProfileUpdate {
  username: string;
  first_name: string | null;
  last_name: string | null;
  avatar_url?: string | null;
}

function avatarRequestOptions(expectedUserId: string) {
  const session = getAuthSession();
  if (!session?.accessToken || session.user?.id !== expectedUserId) {
    throw new Error("Your account changed. Reopen the photo picker and try again.");
  }
  // Capture the initiating token. Never replay a mutation as a newer session.
  return { token: session.accessToken, retryOnUnauthorized: false };
}

export const personalAccountService = {
  chooseAvatar: (source: "google" | "preset" | "none", preset_id: string | undefined, expectedUserId: string) =>
    api.post<{ user: AuthUser }>("/personal/profile/avatar", { source, preset_id }, avatarRequestOptions(expectedUserId)),
  uploadAvatar: (file: File, zoom: number, x: number, y: number, expectedUserId: string) => {
    const form = new FormData();
    form.set("file", file); form.set("zoom", String(zoom)); form.set("x", String(x)); form.set("y", String(y));
    return api.postForm<{ user: AuthUser }>("/personal/profile/avatar/upload", form, avatarRequestOptions(expectedUserId));
  },
  get: () => api.get<PersonalAccount>("/personal/profile"),
  update: (payload: ProfileUpdate) => api.patch<PersonalAccount>("/personal/profile", payload),
};