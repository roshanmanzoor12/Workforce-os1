import type {
  AuthUser,
} from "@/types/auth";

import type {
  AccountEntitlementsPublic,
  CurrentSubscriptionPublic,
  WorkspaceCreationAccessResponse,
} from "@/types/billing";

import type {
  UserWorkspacePublic,
} from "@/types/workspace";

export type AppMode =
  | "personal"
  | "workspace";

export interface AppBootstrapData {
  user:
    AuthUser;

  subscription:
    CurrentSubscriptionPublic;

  entitlements:
    AccountEntitlementsPublic;

  workspaceAccess:
    WorkspaceCreationAccessResponse;

  workspaces:
    UserWorkspacePublic[];

  currentWorkspace:
    UserWorkspacePublic | null;

  mode:
    AppMode;
}