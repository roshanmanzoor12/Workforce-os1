"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import {
  useRouter,
} from "next/navigation";

import {
  ApiError,
  api,
} from "@/lib/api/client";

import {
  clearAuthSession,
  getAuthSession,
  updateStoredUser,
} from "@/lib/auth/session";

import {
  normalizeNavigationView,
} from "@/lib/workspace/access";

import {
  authService,
} from "@/services/auth.service";

import {
  billingService,
} from "@/services/billing.service";

import {
  workspaceAccessService,
} from "@/services/workspace-access.service";

import {
  workspacesService,
} from "@/services/workspaces.service";

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
  WorkspaceMembershipPublic,
  WorkspacePublic,
} from "@/types/workspace";

import type {
  WorkspaceBootstrapResponse,
  WorkspaceFeatureEntitlements,
  WorkspaceNavigationView,
} from "@/types/workspace-access";

import type {
  WorkspaceRolePublic,
} from "@/types/workspace-roles";


const WORKSPACE_STORAGE_KEY =
  "workforce_current_workspace_id";

const APP_MODE_STORAGE_KEY =
  "workforce_app_mode";


const AGENT_RUNTIME_HEARTBEAT_SECONDS =
  15;

type AgentRuntimeStartResponse = {
  session_id: string;
  state?: string;
  device_ids?: string[];
};

type AgentRuntimeResponse = {
  session_id?: string;
  state?: string;
  active?: boolean;
};

export type AppMode =
  | "personal"
  | "workspace";


interface CompatibleWorkspaceRole {
  role_key?: string;

  key?: string;

  display_name?: string;

  name?: string;

  permissions?: string[];

  is_active?: boolean;
}


const PREVIEW_PERMISSIONS:
  Record<
    WorkspaceNavigationView,
    string[]
  > = {
    owner: [
      "*",
    ],

    admin: [
      "workspace.read",
      "workspace.settings.read",
      "workspace.settings.manage",

      "members.read",
      "members.invite",
      "members.update",
      "members.kick",
      "members.ban",
      "members.mute",
      "members.deafen",
      "members.hide",

      "roles.read",
      "roles.assign",
      "roles.manage",

      "employees.all.read",
      "employees.create",
      "employees.update",

      "departments.read",
      "departments.manage",

      "teams.read",
      "teams.manage",

      "attendance.all.read",
      "attendance.manage",
      "attendance.approve",

      "payroll.read",
      "payroll.manage",

      "monitoring.all.read",
      "monitoring.live_screen",

      "devices.all.read",
      "devices.manage",

      "tasks.all.read",
      "tasks.create",
      "tasks.assign.all",
      "tasks.manage",

      "channels.read",
      "channels.create",
      "channels.manage",

      "meetings.read",
      "meetings.create",
      "meetings.invite.all",
      "meetings.manage",

      "reports.all.read",
      "reports.export",

      "integrations.use",
      "integrations.manage",
      "integrations.assign",

      "audit.read",
    ],

    manager: [
      "workspace.read",

      "employees.team.read",

      "departments.read",
      "teams.read",

      "attendance.team.read",
      "attendance.approve",

      "monitoring.team.read",

      "devices.team.read",

      "tasks.team.read",
      "tasks.create",
      "tasks.assign.team",

      "channels.read",

      "meetings.read",
      "meetings.create",
      "meetings.invite.team",

      "reports.team.read",

      "integrations.use",

      "workspace.settings.read",
    ],

    member: [
      "workspace.read",

      "employees.self.read",
      "employees.team.read",

      "departments.read",
      "teams.read",

      "attendance.self.read",

      "compensation.self.read",

      "monitoring.self.read",

      "devices.self.read",

      "tasks.self.read",

      "channels.read",

      "meetings.read",
      "meetings.create",

      "reports.self.read",

      "integrations.use",

      "workspace.settings.read",
    ],

    client: [
      "workspace.read",

      "tasks.self.read",

      "channels.read",

      "meetings.read",

      "reports.self.read",

      "integrations.use",

      "workspace.settings.read",
    ],
  };


function roleKey(
  role:
    WorkspaceRolePublic,
): string {
  const compatible =
    role as unknown as
      CompatibleWorkspaceRole;


  return (
    compatible.role_key ??
    compatible.key ??
    ""
  );
}


export interface WorkspaceContextValue {
  updateUser: (user: AuthUser) => void;
  user:
    AuthUser | null;

  workspaces:
    UserWorkspacePublic[];

  currentWorkspace:
    UserWorkspacePublic | null;

  workspace:
    WorkspacePublic | null;

  membership:
    WorkspaceMembershipPublic | null;

  workspaceId:
    string | null;

  subscription:
    CurrentSubscriptionPublic | null;

  entitlements:
    AccountEntitlementsPublic | null;

  workspaceAccess:
    WorkspaceCreationAccessResponse | null;

  workspaceBootstrap:
    WorkspaceBootstrapResponse | null;

  workspaceRole:
    WorkspaceRolePublic | null;

  availableRoles:
    WorkspaceRolePublic[];

  permissions:
    string[];

  effectivePermissions:
    string[];

  navigationView:
    WorkspaceNavigationView;

  previewNavigationView:
    WorkspaceNavigationView | null;

  effectiveNavigationView:
    WorkspaceNavigationView;

  workspaceEntitlements:
    WorkspaceFeatureEntitlements | null;

  mode:
    AppMode;

  loading:
    boolean;

  workspaceLoading:
    boolean;

  error:
    string | null;

  workspaceError:
    string | null;

  isOwner:
    boolean;

  isAdmin:
    boolean;

  isManager:
    boolean;

  isMember:
    boolean;

  isClient:
    boolean;

  canManage:
    boolean;

  canCreateWorkspace:
    boolean;

  canUseMonitoring:
    boolean;

  canUseLiveScreen:
    boolean;

  canUseAdvancedAnalytics:
    boolean;

  switchWorkspace: (
    workspaceId:
      string,
  ) => void;

  enterPersonalMode:
    () => void;

  setRolePreview: (
    view:
      WorkspaceNavigationView,
  ) => void;

  clearRolePreview:
    () => void;

  openCreatedWorkspace: (workspaceId: string) => Promise<void>;

  refreshWorkspaces:
    () => Promise<void>;

  refreshBootstrap:
    () => Promise<void>;

  refreshBilling:
    () => Promise<void>;

  refreshWorkspaceAccess:
    () => Promise<void>;
}


const WorkspaceContext =
  createContext<WorkspaceContextValue | null>(
    null,
  );


function readStoredMode():
  AppMode | null {
  if (
    typeof window ===
    "undefined"
  ) {
    return null;
  }


  const value =
    window.localStorage.getItem(
      APP_MODE_STORAGE_KEY,
    );


  if (
    value ===
      "personal" ||
    value ===
      "workspace"
  ) {
    return value;
  }


  return null;
}


function storeMode(
  value:
    AppMode,
): void {
  if (
    typeof window ===
    "undefined"
  ) {
    return;
  }


  window.localStorage.setItem(
    APP_MODE_STORAGE_KEY,
    value,
  );
}


function readStoredWorkspaceId():
  string | null {
  if (
    typeof window ===
    "undefined"
  ) {
    return null;
  }


  return window.localStorage.getItem(
    WORKSPACE_STORAGE_KEY,
  );
}


function storeWorkspaceId(
  workspaceId:
    string,
): void {
  if (
    typeof window ===
    "undefined"
  ) {
    return;
  }


  window.localStorage.setItem(
    WORKSPACE_STORAGE_KEY,
    workspaceId,
  );
}


function clearStoredWorkspaceId():
  void {
  if (
    typeof window ===
    "undefined"
  ) {
    return;
  }


  window.localStorage.removeItem(
    WORKSPACE_STORAGE_KEY,
  );
}


export function WorkspaceProvider({
  children,
}: {
  children:
    React.ReactNode;
}) {
  const router =
    useRouter();


  const initialLoadStarted =
    useRef(
      false,
    );


  const workspaceRequestSequence =
    useRef(
      0,
    );


  const [
    user,
    setUser,
  ] =
    useState<AuthUser | null>(
      null,
    );


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
    subscription,
    setSubscription,
  ] =
    useState<CurrentSubscriptionPublic | null>(
      null,
    );


  const [
    entitlements,
    setEntitlements,
  ] =
    useState<AccountEntitlementsPublic | null>(
      null,
    );


  const [
    workspaceAccess,
    setWorkspaceAccess,
  ] =
    useState<WorkspaceCreationAccessResponse | null>(
      null,
    );


  const [
    workspaceBootstrap,
    setWorkspaceBootstrap,
  ] =
    useState<WorkspaceBootstrapResponse | null>(
      null,
    );


  const [
    previewNavigationView,
    setPreviewNavigationView,
  ] =
    useState<WorkspaceNavigationView | null>(
      null,
    );


  const [
    mode,
    setMode,
  ] =
    useState<AppMode>(
      "personal",
    );


  const [
    loading,
    setLoading,
  ] =
    useState(
      true,
    );


  const [
    workspaceLoading,
    setWorkspaceLoading,
  ] =
    useState(
      false,
    );


  const [
    error,
    setError,
  ] =
    useState<string | null>(
      null,
    );


  const [
    workspaceError,
    setWorkspaceError,
  ] =
    useState<string | null>(
      null,
    );


  const resolveWorkspaceSelection =
    useCallback(
      (
        items:
          UserWorkspacePublic[],
      ) => {
        const active =
          items.filter(
            (item) =>
              item.membership
                .status ===
              "active",
          );


        if (
          active.length ===
          0
        ) {
          setCurrentWorkspaceId(
            null,
          );

          setWorkspaceBootstrap(
            null,
          );

          setPreviewNavigationView(
            null,
          );

          setMode(
            "personal",
          );

          clearStoredWorkspaceId();

          storeMode(
            "personal",
          );

          return;
        }


        const savedMode =
          readStoredMode();


        if (
          savedMode ===
          "personal"
        ) {
          setCurrentWorkspaceId(
            null,
          );

          setWorkspaceBootstrap(
            null,
          );

          setPreviewNavigationView(
            null,
          );

          setMode(
            "personal",
          );

          return;
        }


        const savedWorkspaceId =
          readStoredWorkspaceId();


        const savedWorkspace =
          savedWorkspaceId
            ? active.find(
                (item) =>
                  item.workspace.id ===
                  savedWorkspaceId,
              )
            : undefined;


        const readyWorkspace =
          active.find(
            (item) =>
              item.workspace
                .status ===
              "ready",
          );


        const selected =
          savedWorkspace ??
          readyWorkspace ??
          active[0];


        if (
          !selected
        ) {
          return;
        }


        const selectedId =
          selected.workspace.id;


        setCurrentWorkspaceId(
          selectedId,
        );

        setMode(
          "workspace",
        );

        storeMode(
          "workspace",
        );

        storeWorkspaceId(
          selectedId,
        );
      },
      [],
    );


    const billingRequestSequence = useRef(0);
    const userRevision = useRef(0);
    const agentRuntimeRef = useRef<{
      workspaceId: string;
      sessionId: string;
    } | null>(null);
    const agentRuntimeGeneration = useRef(0);

    const updateUser = useCallback((next: AuthUser) => {
      if (getAuthSession()?.user?.id !== next.id) return;
      userRevision.current += 1;
      updateStoredUser(next);
      setUser(current => current?.id === next.id ? next : current);
      window.dispatchEvent(new CustomEvent("workforce:profile-updated", { detail: next.id }));
    }, []);

    const refreshBootstrap = useCallback(async () => {
    if (!getAuthSession()?.accessToken) {
      clearAuthSession();
      setUser(null);
      setLoading(false);
      router.replace("/login");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const readRevision = userRevision.current;
      const readOwner = getAuthSession()?.user?.id;
      const currentUser = await authService.getVerifiedCurrentUser();
      if (readRevision === userRevision.current && (!readOwner || getAuthSession()?.user?.id === readOwner)) {
        setUser(currentUser.user);
      }

      const billingRequestId = ++billingRequestSequence.current;
      const [workspaceResult, subscriptionResult, entitlementResult, accessResult] =
        await Promise.allSettled([
          workspacesService.list(),
          billingService.getSubscription(),
          billingService.getEntitlements(),
          billingService.getWorkspaceAccess(),
        ]);

      const results = [workspaceResult, subscriptionResult, entitlementResult, accessResult];
      for (const result of results) {
        if (result.status === "rejected" && result.reason instanceof ApiError && result.reason.status === 401) {
          throw result.reason;
        }
      }

      const failures: string[] = [];
      if (workspaceResult.status === "fulfilled") {
        setWorkspaces(workspaceResult.value.workspaces);
        resolveWorkspaceSelection(workspaceResult.value.workspaces);
      } else {
        failures.push("Workspace memberships could not be loaded.");
      }

      if (billingRequestId === billingRequestSequence.current) {
        if (subscriptionResult.status === "fulfilled") {
          setSubscription(subscriptionResult.value);
        } else {
          setSubscription(null);
          failures.push("Your plan could not be loaded.");
        }
  
        if (entitlementResult.status === "fulfilled") {
          setEntitlements(entitlementResult.value);
        } else {
          setEntitlements(null);
          failures.push("Account entitlements could not be loaded.");
        }
  
        if (accessResult.status === "fulfilled") {
          setWorkspaceAccess(accessResult.value);
        } else {
          setWorkspaceAccess(null);
          failures.push("Workspace creation eligibility could not be loaded.");
        }
      }

      setError(failures.length ? `${failures.join(" ")} Retry account details.` : null);
    } catch (cause) {
      if (cause instanceof ApiError && cause.status === 401) {
        clearAuthSession();
        setUser(null);
        setWorkspaces([]);
        setCurrentWorkspaceId(null);
        setWorkspaceBootstrap(null);
        setSubscription(null);
        setEntitlements(null);
        setWorkspaceAccess(null);
        router.replace("/login");
        return;
      }
      setUser(null);
      setError("Your account could not be verified. Please retry.");
    } finally {
      setLoading(false);
    }
  }, [resolveWorkspaceSelection, router]);


  const refreshBilling = useCallback(async () => {
    const ownerId = getAuthSession()?.user?.id;
    if (!ownerId || !getAuthSession()?.accessToken) return;
    const requestId = ++billingRequestSequence.current;
    const [nextSubscription, nextEntitlements, nextAccess] = await Promise.all([
      billingService.getSubscription(),
      billingService.getEntitlements(),
      billingService.getWorkspaceAccess(),
    ]);
    if (requestId !== billingRequestSequence.current ||
        getAuthSession()?.user?.id !== ownerId) return;
    setSubscription(nextSubscription);
    setEntitlements(nextEntitlements);
    setWorkspaceAccess(nextAccess);
  }, []);


  const refreshWorkspaceAccess =
    useCallback(
      async () => {
        const workspaceId =
          currentWorkspaceId;


        if (
          mode !==
            "workspace" ||
          !workspaceId
        ) {
          workspaceRequestSequence.current +=
            1;

          setWorkspaceBootstrap(
            null,
          );

          setWorkspaceError(
            null,
          );

          setWorkspaceLoading(
            false,
          );

          setPreviewNavigationView(
            null,
          );

          return;
        }


        const requestId =
          workspaceRequestSequence.current +
          1;


        workspaceRequestSequence.current =
          requestId;


        try {
          setWorkspaceLoading(
            true,
          );

          setWorkspaceError(
            null,
          );


          const response =
            await workspaceAccessService
              .getBootstrap(
                workspaceId,
              );


          if (
            workspaceRequestSequence
              .current !==
            requestId
          ) {
            return;
          }


          setWorkspaceBootstrap(
            response,
          );

        } catch (
          cause
        ) {
          if (
            workspaceRequestSequence
              .current !==
            requestId
          ) {
            return;
          }


          if (
            cause instanceof
              ApiError &&
            cause.status ===
              401
          ) {
            clearAuthSession();

            router.replace(
              "/login",
            );

            return;
          }


          if (
            cause instanceof
              ApiError &&
            cause.status ===
              403
          ) {
            setWorkspaceBootstrap(
              null,
            );

            setCurrentWorkspaceId(
              null,
            );

            setPreviewNavigationView(
              null,
            );

            setMode(
              "personal",
            );

            clearStoredWorkspaceId();

            storeMode(
              "personal",
            );

            router.replace(
              "/home",
            );

            return;
          }


          setWorkspaceBootstrap(
            null,
          );

          setWorkspaceError(
            cause instanceof Error
              ? cause.message
              : "Unable to load workspace access.",
          );

        } finally {
          if (
            workspaceRequestSequence
              .current ===
            requestId
          ) {
            setWorkspaceLoading(
              false,
            );
          }
        }
      },
      [
        currentWorkspaceId,
        mode,
        router,
      ],
    );


  const refreshWorkspaces =
    useCallback(
      async () => {
        try {
          setError(
            null,
          );


          const response =
            await workspacesService
              .list();


          setWorkspaces(
            response.workspaces,
          );


          resolveWorkspaceSelection(
            response.workspaces,
          );

        } catch (
          cause
        ) {
          if (
            cause instanceof
              ApiError &&
            cause.status ===
              401
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
              : "Unable to refresh workspaces.",
          );
        }
      },
      [
        resolveWorkspaceSelection,
        router,
      ],
    );


  useEffect(
    () => {
      if (
        initialLoadStarted.current
      ) {
        return;
      }


      initialLoadStarted.current =
        true;


      void refreshBootstrap();
    },
    [
      refreshBootstrap,
    ],
  );


  useEffect(
    () => {
      void refreshWorkspaceAccess();
    },
    [
      refreshWorkspaceAccess,
    ],
  );


  useEffect(() => {
    if (!user?.id) return;
    const owner = user.id;
    let stopped = false;
    let running = false;
    async function syncPhoto() {
      if (stopped || running || document.hidden) return;
      running = true;
      const readRevision = userRevision.current;
      try {
        const result = await authService.getVerifiedCurrentUser();
        if (!stopped && readRevision === userRevision.current && result.user.id === owner && getAuthSession()?.user?.id === owner) {
          updateStoredUser(result.user);
          setUser(current => current?.id === owner ? result.user : current);
        }
      } catch { /* Keep the current photo during a temporary connection failure. */ }
      finally { running = false; }
    }
    const resume = () => { void syncPhoto(); };
    window.addEventListener("focus", resume);
    document.addEventListener("visibilitychange", resume);
    const timer = window.setInterval(resume, 60000);
    return () => { stopped = true; window.clearInterval(timer); window.removeEventListener("focus", resume); document.removeEventListener("visibilitychange", resume); };
  }, [user?.id]);

  useEffect(() => {
    const runtimeWorkspaceId = currentWorkspaceId;
    const runtimeUserId = user?.id;
    const authSession = getAuthSession();

    if (
      mode !== "workspace" ||
      !runtimeWorkspaceId ||
      !runtimeUserId ||
      !authSession?.accessToken
    ) {
      return;
    }

    const generation =
      agentRuntimeGeneration.current + 1;

    agentRuntimeGeneration.current =
      generation;

    let cancelled = false;
    let stopping = false;
    let heartbeatTimer: number | null = null;

    const stopRuntime = async () => {
      if (stopping) return;

      stopping = true;

      if (heartbeatTimer !== null) {
        window.clearInterval(heartbeatTimer);
        heartbeatTimer = null;
      }

      const current =
        agentRuntimeRef.current;

      if (
        !current ||
        current.workspaceId !==
          runtimeWorkspaceId
      ) {
        return;
      }

      agentRuntimeRef.current =
        null;

      try {
        await api.post(
          `/workspaces/${runtimeWorkspaceId}/agent-runtime/stop`,
          {
            session_id: current.sessionId,
          },
        );
      } catch {
        // The backend TTL will expire this runtime if the page closes.
      }
    };

    const sendHeartbeat = async () => {
      if (cancelled || stopping) return;

      const current =
        agentRuntimeRef.current;

      if (
        !current ||
        current.workspaceId !==
          runtimeWorkspaceId
      ) {
        return;
      }

      try {
        await api.post<AgentRuntimeResponse>(
          `/workspaces/${runtimeWorkspaceId}/agent-runtime/heartbeat`,
          {
            session_id: current.sessionId,
          },
        );
      } catch {
        // A temporary failure is retried on the next heartbeat.
      }
    };

    const startRuntime = async () => {
      try {
        const response =
          await api.post<AgentRuntimeStartResponse>(
            `/workspaces/${runtimeWorkspaceId}/agent-runtime/start`,
            {},
          );

        if (
          cancelled ||
          agentRuntimeGeneration.current !==
            generation
        ) {
          try {
            await api.post(
              `/workspaces/${runtimeWorkspaceId}/agent-runtime/stop`,
              {
                session_id: response.session_id,
              },
            );
          } catch {
            // The backend TTL handles an abandoned start request.
          }

          return;
        }

        agentRuntimeRef.current = {
          workspaceId: runtimeWorkspaceId,
          sessionId: response.session_id,
        };

        await sendHeartbeat();

        heartbeatTimer = window.setInterval(
          () => {
            void sendHeartbeat();
          },
          AGENT_RUNTIME_HEARTBEAT_SECONDS *
            1000,
        );
      } catch {
        // Keep workspace navigation usable while the runtime endpoint is unavailable.
      }
    };

    void startRuntime();

    return () => {
      cancelled = true;
      void stopRuntime();
    };
  }, [
    currentWorkspaceId,
    mode,
    user?.id,
  ]);

  const currentWorkspace =
    useMemo<
      UserWorkspacePublic | null
    >(
      () => {
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
          ) ??
          null
        );
      },
      [
        currentWorkspaceId,
        workspaces,
      ],
    );


  const workspace =
    currentWorkspace
      ?.workspace ??
    null;


  const membership =
    currentWorkspace
      ?.membership ??
    null;


  // Ignore an older workspace's bootstrap while a switch is in flight.
  const verifiedBootstrap =
    workspaceBootstrap?.workspace_id === currentWorkspaceId &&
    workspaceBootstrap?.membership_id === membership?.id
      ? workspaceBootstrap
      : null;

  const activeRoleKey =
    membership?.role_key ?? "member";


  const navigationView =
    normalizeNavigationView(
      activeRoleKey,
    );


  const permissions =
    verifiedBootstrap?.permissions ?? [];


  const availableRoles =
    verifiedBootstrap?.available_roles ?? [];


  const workspaceRole =
    availableRoles.find(
      (role) =>
        roleKey(
          role,
        ) ===
        activeRoleKey,
    ) ??
    null;


  const effectiveNavigationView =
    verifiedBootstrap &&
    navigationView ===
      "owner" &&
    previewNavigationView
      ? previewNavigationView
      : navigationView;


  const effectivePermissions =
    verifiedBootstrap &&
    navigationView ===
      "owner" &&
    previewNavigationView
      ? [
          ...PREVIEW_PERMISSIONS[
            previewNavigationView
          ],
        ]
      : permissions;


  const workspaceEntitlements: WorkspaceFeatureEntitlements | null =
    mode === "workspace"
      ? verifiedBootstrap?.billing
        ? {
            plan_code: verifiedBootstrap.billing.plan_code,
            monitoring: verifiedBootstrap.billing.features.monitoring,
            live_screen: verifiedBootstrap.billing.features.live_screen,
            advanced_analytics: verifiedBootstrap.billing.features.advanced_analytics,
          }
        : null
      : entitlements
        ? {
            plan_code: entitlements.plan_code,
            monitoring: entitlements.monitoring,
            live_screen: entitlements.live_screen,
            advanced_analytics: entitlements.advanced_analytics,
          }
        : null;

  const canUseMonitoring = workspaceEntitlements?.monitoring ?? false;
  const canUseLiveScreen = workspaceEntitlements?.live_screen ?? false;
  const canUseAdvancedAnalytics = workspaceEntitlements?.advanced_analytics ?? false;

  const openCreatedWorkspace = useCallback(async (workspaceId: string) => {
    const ownerId = getAuthSession()?.user?.id;
    const response = await workspacesService.list();
    if (!ownerId || getAuthSession()?.user?.id !== ownerId) return;
    const record = response.workspaces.find(item => item.workspace.id === workspaceId &&
      item.membership.status === "active" && item.workspace.is_active && item.workspace.status === "ready");
    if (!record) throw new Error("The workspace is not ready yet. Refresh its setup status.");
    workspaceRequestSequence.current += 1;
    setWorkspaces(response.workspaces);
    setWorkspaceBootstrap(null);
    setWorkspaceError(null);
    setPreviewNavigationView(null);
    setCurrentWorkspaceId(workspaceId);
    setMode("workspace");
    storeWorkspaceId(workspaceId);
    storeMode("workspace");
    router.push("/dashboard");
  }, [router]);

  const switchWorkspace =
    useCallback(
      (
        workspaceId:
          string,
      ) => {
        const target =
          workspaces.find(
            (item) =>
              item.workspace.id ===
                workspaceId &&
              item.membership
                .status ===
                "active",
          );


        if (
          !target
        ) {
          return;
        }


        workspaceRequestSequence.current +=
          1;


        storeMode(
          "workspace",
        );

        storeWorkspaceId(
          workspaceId,
        );


        setPreviewNavigationView(
          null,
        );

        setWorkspaceBootstrap(
          null,
        );

        setWorkspaceError(
          null,
        );

        setCurrentWorkspaceId(
          workspaceId,
        );

        setMode(
          "workspace",
        );


        router.push(
          "/dashboard",
        );
      },
      [
        router,
        workspaces,
      ],
    );


  const enterPersonalMode =
    useCallback(
      () => {
        workspaceRequestSequence.current +=
          1;


        storeMode(
          "personal",
        );


        setMode(
          "personal",
        );

        setCurrentWorkspaceId(
          null,
        );

        setWorkspaceBootstrap(
          null,
        );

        setPreviewNavigationView(
          null,
        );

        setWorkspaceError(
          null,
        );

        setWorkspaceLoading(
          false,
        );


        router.push(
          "/home",
        );
      },
      [
        router,
      ],
    );


  const setRolePreview =
    useCallback(
      (
        view:
          WorkspaceNavigationView,
      ) => {
        if (
          navigationView !==
          "owner"
        ) {
          return;
        }


        if (
          view ===
          "owner"
        ) {
          setPreviewNavigationView(
            null,
          );

          return;
        }


        setPreviewNavigationView(
          view,
        );
      },
      [
        navigationView,
      ],
    );


  const clearRolePreview =
    useCallback(
      () => {
        setPreviewNavigationView(
          null,
        );
      },
      [],
    );


  const value =
    useMemo<WorkspaceContextValue>(
      () => ({
        updateUser,
        user,

        workspaces,

        currentWorkspace,

        workspace,

        membership,

        workspaceId:
          workspace?.id ??
          null,

        subscription,

        entitlements,

        workspaceAccess,

        workspaceBootstrap: verifiedBootstrap,

        workspaceRole,

        availableRoles,

        permissions,

        effectivePermissions,

        navigationView,

        previewNavigationView,

        effectiveNavigationView,

        workspaceEntitlements,

        mode,

        loading,

        workspaceLoading,

        error,

        workspaceError,

        isOwner:
          navigationView ===
          "owner",

        isAdmin:
          navigationView ===
          "admin",

        isManager:
          navigationView ===
          "manager",

        isMember:
          navigationView ===
          "member",

        isClient:
          navigationView ===
          "client",

        canManage:
          navigationView ===
            "owner" ||
          navigationView ===
            "admin",

        canCreateWorkspace:
          workspaceAccess
            ?.allowed ??
          false,

        canUseMonitoring,

        canUseLiveScreen,

        canUseAdvancedAnalytics,

        switchWorkspace,

        openCreatedWorkspace,

        enterPersonalMode,

        setRolePreview,

        clearRolePreview,

        refreshWorkspaces,

        refreshBootstrap,

        refreshBilling,

        refreshWorkspaceAccess,
      }),
      [
        updateUser,
        user,
        workspaces,
        currentWorkspace,
        workspace,
        membership,
        subscription,
        entitlements,
        workspaceAccess,
        workspaceBootstrap,
        workspaceRole,
        availableRoles,
        permissions,
        effectivePermissions,
        navigationView,
        previewNavigationView,
        effectiveNavigationView,
        workspaceEntitlements,
        mode,
        loading,
        workspaceLoading,
        error,
        workspaceError,
        canUseMonitoring,
        canUseLiveScreen,
        canUseAdvancedAnalytics,
        switchWorkspace,
        openCreatedWorkspace,
        enterPersonalMode,
        setRolePreview,
        clearRolePreview,
        refreshWorkspaces,
        refreshBootstrap,
        refreshBilling,
        refreshWorkspaceAccess,
      ],
    );


  return (
    <WorkspaceContext.Provider
      value={
        value
      }
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


  if (
    !context
  ) {
    throw new Error(
      "useWorkspace must be used inside WorkspaceProvider.",
    );
  }


  return context;
}
