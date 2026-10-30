"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import { useRouter } from "next/navigation";

import { ApiError } from "@/lib/api/client";

import {
  clearAuthSession,
  getAuthSession,
} from "@/lib/auth/session";

import { workspacesService } from "@/services/workspaces.service";

import type {
  UserWorkspacePublic,
  WorkspaceMembershipPublic,
  WorkspacePublic,
} from "@/types/workspace";

const WORKSPACE_STORAGE_KEY =
  "workforce_current_workspace_id";

interface WorkspaceContextValue {
  workspaces: UserWorkspacePublic[];

  currentWorkspace:
    UserWorkspacePublic | null;

  workspace:
    WorkspacePublic | null;

  membership:
    WorkspaceMembershipPublic | null;

  workspaceId: string | null;

  loading: boolean;

  error: string | null;

  isOwner: boolean;
  isAdmin: boolean;
  canManage: boolean;

  switchWorkspace: (
    workspaceId: string,
  ) => void;

  refreshWorkspaces:
    () => Promise<void>;
}

const WorkspaceContext =
  createContext<WorkspaceContextValue | null>(
    null,
  );

export function WorkspaceProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const router =
    useRouter();

  const [
    workspaces,
    setWorkspaces,
  ] =
    useState<UserWorkspacePublic[]>(
      [],
    );

  const [
    currentWorkspaceId,
    setCurrentWorkspaceId,
  ] =
    useState<string | null>(
      null,
    );

  const [
    loading,
    setLoading,
  ] =
    useState(true);

  const [
    error,
    setError,
  ] =
    useState<string | null>(
      null,
    );

  const loadWorkspaces =
    useCallback(
      async () => {
        const session =
          getAuthSession();

        if (
          !session?.accessToken
        ) {
          clearAuthSession();

          router.replace(
            "/login",
          );

          return;
        }

        try {
          setLoading(true);

          setError(null);

          const response =
            await workspacesService.list();

          setWorkspaces(
            response.workspaces,
          );

          if (
            response.workspaces
              .length === 0
          ) {
            setCurrentWorkspaceId(
              null,
            );

            return;
          }

          const storedId =
            typeof window !==
            "undefined"
              ? window.localStorage.getItem(
                  WORKSPACE_STORAGE_KEY,
                )
              : null;

          const storedWorkspace =
            storedId
              ? response.workspaces.find(
                  (item) =>
                    item.workspace
                      .id ===
                      storedId &&
                    item.membership
                      .status ===
                      "active",
                )
              : undefined;

          const readyWorkspace =
            response.workspaces.find(
              (item) =>
                item.membership
                  .status ===
                  "active" &&
                item.workspace
                  .status ===
                  "ready",
            );

          const activeWorkspace =
            response.workspaces.find(
              (item) =>
                item.membership
                  .status ===
                "active",
            );

          const preferredWorkspace =
            storedWorkspace ??
            readyWorkspace ??
            activeWorkspace ??
            response.workspaces[0];

          if (
            !preferredWorkspace
          ) {
            setCurrentWorkspaceId(
              null,
            );

            return;
          }

          const selectedId =
            preferredWorkspace
              .workspace.id;

          setCurrentWorkspaceId(
            selectedId,
          );

          if (
            typeof window !==
            "undefined"
          ) {
            window.localStorage.setItem(
              WORKSPACE_STORAGE_KEY,
              selectedId,
            );
          }
        } catch (cause) {
          if (
            cause instanceof
              ApiError &&
            cause.status === 401
          ) {
            clearAuthSession();

            router.replace(
              "/login",
            );

            return;
          }

          setError(
            cause instanceof Error
              ? cause.message
              : "Unable to load workspaces.",
          );
        } finally {
          setLoading(false);
        }
      },
      [router],
    );

  useEffect(() => {
    void loadWorkspaces();
  }, [loadWorkspaces]);

  const currentWorkspace =
    useMemo<
      UserWorkspacePublic | null
    >(() => {
      if (
        !currentWorkspaceId
      ) {
        return null;
      }

      return (
        workspaces.find(
          (item) =>
            item.workspace.id ===
            currentWorkspaceId,
        ) ?? null
      );
    }, [
      currentWorkspaceId,
      workspaces,
    ]);

  const switchWorkspace =
    useCallback(
      (
        workspaceId: string,
      ) => {
        const target =
          workspaces.find(
            (item) =>
              item.workspace.id ===
              workspaceId,
          );

        if (!target) {
          return;
        }

        if (
          target.membership
            .status !== "active"
        ) {
          return;
        }

        setCurrentWorkspaceId(
          workspaceId,
        );

        if (
          typeof window !==
          "undefined"
        ) {
          window.localStorage.setItem(
            WORKSPACE_STORAGE_KEY,
            workspaceId,
          );
        }
      },
      [workspaces],
    );

  const workspace =
    currentWorkspace
      ?.workspace ?? null;

  const membership =
    currentWorkspace
      ?.membership ?? null;

  const role =
    membership?.role_key ??
    null;

  const value =
    useMemo<WorkspaceContextValue>(
      () => ({
        workspaces,

        currentWorkspace,

        workspace,

        membership,

        workspaceId:
          workspace?.id ??
          null,

        loading,

        error,

        isOwner:
          role === "owner",

        isAdmin:
          role === "admin",

        canManage:
          role === "owner" ||
          role === "admin",

        switchWorkspace,

        refreshWorkspaces:
          loadWorkspaces,
      }),
      [
        workspaces,
        currentWorkspace,
        workspace,
        membership,
        loading,
        error,
        role,
        switchWorkspace,
        loadWorkspaces,
      ],
    );

  return (
    <WorkspaceContext.Provider
      value={value}
    >
      {children}
    </WorkspaceContext.Provider>
  );
}

export function useWorkspace():
  WorkspaceContextValue {
  const context =
    useContext(
      WorkspaceContext,
    );

  if (!context) {
    throw new Error(
      "useWorkspace must be used inside WorkspaceProvider.",
    );
  }

  return context;
}