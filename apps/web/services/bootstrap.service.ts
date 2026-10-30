import {
  clearLastWorkspaceId,
  getLastWorkspaceId,
} from "@/lib/app/bootstrap-storage";

import {
  authService,
} from "@/services/auth.service";

import {
  billingService,
} from "@/services/billing.service";

import {
  workspaceService,
} from "@/services/workspace.service";

import type {
  AppBootstrapData,
} from "@/types/bootstrap";

import type {
  UserWorkspacePublic,
} from "@/types/workspace";

function resolveWorkspace(
  workspaces:
    UserWorkspacePublic[],
): UserWorkspacePublic | null {
  if (
    workspaces.length ===
    0
  ) {
    clearLastWorkspaceId();

    return null;
  }

  const lastWorkspaceId =
    getLastWorkspaceId();

  if (
    lastWorkspaceId
  ) {
    const found =
      workspaces.find(
        (item) =>
          item.workspace.id ===
          lastWorkspaceId,
      );

    if (found) {
      return found;
    }

    clearLastWorkspaceId();
  }

  if (
    workspaces.length ===
    1
  ) {
    return (
      workspaces[0] ??
      null
    );
  }

  return null;
}

export async function loadAppBootstrap():
  Promise<AppBootstrapData> {
  const [
    currentUser,
    subscription,
    entitlements,
    workspaceAccess,
    workspaceList,
  ] =
    await Promise.all([
      authService
        .getVerifiedCurrentUser(),

      billingService
        .getSubscription(),

      billingService
        .getEntitlements(),

      billingService
        .getWorkspaceAccess(),

      workspaceService
        .list(),
    ]);

  const currentWorkspace =
    resolveWorkspace(
      workspaceList.workspaces,
    );

  return {
    user:
      currentUser.user,

    subscription,

    entitlements,

    workspaceAccess,

    workspaces:
      workspaceList.workspaces,

    currentWorkspace,

    mode:
      currentWorkspace
        ? "workspace"
        : "personal",
  };
}