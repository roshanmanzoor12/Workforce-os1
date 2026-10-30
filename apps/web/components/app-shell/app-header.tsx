"use client";

import {
  Bell,
  Search,
} from "lucide-react";

import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { workspaceInvitationsService } from "@/services/workspace-invitations.service";

import {
  AccountMenu,
} from "@/components/account/account-menu";

import {
  WorkspaceSwitcher,
} from "@/components/app-shell/workspace-switcher";

import { workspacePageLabel } from "@/lib/workspace/templates";

import {
  useWorkspace,
} from "@/contexts/workspace-context";


interface AppHeaderProps {
  workspaceName?: string | null;
  userName?: string | null;
  userRole?: string | null;
  avatarUrl?: string | null;
  notificationCount?: number;
}


const routeLabels: Record<string, string> = {
  home: "Home",
  dashboard: "Dashboard",
  profile: "Profile",
  friends: "Friends",
  messages: "Personal Messages",
  chat: "Personal Messages",
  groups: "Groups",
  calls: "Personal Calls",
  notes: "Notes",
  goals: "Goals",
  ai: "Personal AI",
  activities: "Activities",
  billing: "Personal Billing",
  settings: "Settings",

  employees: "Employees",
  departments: "Departments",
  attendance: "Attendance & Time Tracking",
  payroll: "Payroll",
  monitoring: "Monitoring / Activity",
  devices: "Devices",
  tasks: "Tasks",
  channels: "Channels & Chat",
  meetings: "Meetings & Calls",
  reports: "Reports & Analytics",
  integrations: "Integrations",
  workspaces: "Workspaces",
};


function getBreadcrumbLabel(
  pathname: string,
  mode: "personal" | "workspace",
): string {
  const segment = pathname
    .split("/")
    .filter(Boolean)[0];

  if (!segment) {
    return "Home";
  }

  if (mode === "workspace") {
    const workspaceLabels: Record<string, string> = {
      dashboard: "Dashboard",
      employees: "Employees",
      departments: "Departments",
      attendance: "Attendance & Time Tracking",
      payroll: "Payroll",
      monitoring: "Monitoring / Activity",
      devices: "Devices",
      tasks: "Tasks",
      channels: "Channels & Chat",
      chat: "Messages",
      messages: "Messages",
      calls: "Calls",
      meetings: "Meetings & Calls",
      reports: "Reports & Analytics",
      integrations: "Integrations",
      billing: "Plans & Billing",
      settings: "Settings",
      workspaces: "Workspaces",
    };

    if (workspaceLabels[segment]) {
      return workspaceLabels[segment];
    }
  }

  if (routeLabels[segment]) {
    return routeLabels[segment];
  }

  return segment
    .split("-")
    .map(
      (part) =>
        part.charAt(0).toUpperCase() +
        part.slice(1),
    )
    .join(" ");
}


export function AppHeader({
  userName,
  userRole,
  avatarUrl,
  notificationCount = 0,
}: AppHeaderProps) {
  const pathname = usePathname();
  const router = useRouter();
  const [incomingCount, setIncomingCount] = useState(0);
  useEffect(() => {
    let mounted = true;
    const update = async () => {
      try {
        const result = await workspaceInvitationsService.incoming();
        if (mounted) setIncomingCount(result.total);
      } catch { if (mounted) setIncomingCount(0); }
    };
    void update();
    const timer = window.setInterval(() => { if (!document.hidden) void update(); }, 15000);
    return () => { mounted = false; window.clearInterval(timer); };
  }, [pathname]);
  const totalNotificationCount = notificationCount + incomingCount;

  const {
    mode,
    workspace,
    membership,
    user,
  } = useWorkspace();

  const currentLabel = (mode === "workspace" ? (pathname === "/dashboard" ? "Home" : workspacePageLabel(pathname, workspace?.workspace_type)) : undefined) ?? getBreadcrumbLabel(
    pathname,
    mode,
  );

  const rootLabel =
    mode === "workspace"
      ? "Workspace"
      : "Personal";

  const isRootPage =
    pathname === "/home" ||
    pathname === "/dashboard" ||
    pathname === "/personal";

  const resolvedName =
    userName ??
    (user
      ? [
          user.first_name,
          user.last_name,
        ]
          .filter(Boolean)
          .join(" ") ||
        user.username
      : null);

  const resolvedRole =
    mode === "workspace"
      ? membership?.role_key ?? userRole
      : userRole;

  const resolvedAvatar = user
    ? user.avatar_url
    : avatarUrl ?? null;

  return (
    <header
      style={{
        position: "sticky",
        top: 0,
        zIndex: "var(--z-sticky)",
        display: "flex",
        height: "var(--header-height)",
        alignItems: "center",
        gap: 18,
        paddingRight: 18,
        borderBottom: `2px solid ${mode === "workspace" ? (workspace?.primary_color ?? "#2563EB") : "var(--color-border)"}`,
        background: "var(--color-header-background)",
        backdropFilter: "blur(8px)",
      }}
    >
      <div
        style={{
          minWidth: 0,
          flex: "1 1 auto",
          paddingLeft: 28,
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 9,
            overflow: "hidden",
            color: "#7a7e82",
            fontSize: 12,
          }}
        >
          <span
            style={{
              maxWidth: 220,
              overflow: "hidden",
              color: "#2e3134",
              fontWeight: 500,
              whiteSpace: "nowrap",
              textOverflow: "ellipsis",
            }}
          >
            {rootLabel}
          </span>

          {!isRootPage || mode === "workspace" ? (
            <>
              <span
                aria-hidden="true"
                style={{
                  color: "#b1aca2",
                }}
              >
                /
              </span>

              <span
                style={{
                  overflow: "hidden",
                  whiteSpace: "nowrap",
                  textOverflow: "ellipsis",
                }}
              >
                {currentLabel}
              </span>
            </>
          ) : null}
        </div>
      </div>

      <WorkspaceSwitcher />

      <div
        role="search"
        style={{
          position: "relative",
          width: 250,
        }}
      >
        <Search
          aria-hidden="true"
          size={15}
          strokeWidth={1.8}
          style={{
            position: "absolute",
            top: "50%",
            left: 12,
            color: "#7d8085",
            transform: "translateY(-50%)",
            pointerEvents: "none",
          }}
        />

        <input
          type="search"
          aria-label="Search Workforce OS"
          placeholder="Search"
          style={{
            width: "100%",
            height: 36,
            padding: "0 36px",
            border: "1px solid var(--color-border)",
            borderRadius: 8,
            outline: "none",
            background: "#fffefa",
            color: "#303235",
            fontSize: 12,
          }}
        />
      </div>

      <button
        type="button"
        aria-label="Notifications"
        onClick={() => router.push("/friends?tab=invitations")}
        style={{
          position: "relative",
          display: "grid",
          width: 36,
          height: 36,
          flex: "0 0 auto",
          placeItems: "center",
          border: "1px solid var(--color-border)",
          borderRadius: 8,
          background: "#fffefa",
          color: "#333639",
          cursor: "pointer",
        }}
      >
        <Bell
          size={17}
          strokeWidth={1.7}
        />

        {totalNotificationCount > 0 ? (
          <span
            aria-label={`${totalNotificationCount} notifications`}
            style={{
              position: "absolute",
              top: -5,
              right: -5,
              display: "grid",
              minWidth: 17,
              height: 17,
              paddingInline: 4,
              placeItems: "center",
              border: "2px solid var(--color-app-background)",
              borderRadius: 999,
              background: "#f8b916",
              color: "#2a2600",
              fontSize: 9,
              fontWeight: 700,
              lineHeight: 1,
            }}
          >
            {totalNotificationCount > 99
              ? "99+"
              : totalNotificationCount}
          </span>
        ) : null}
      </button>

      <AccountMenu
        initialUserName={resolvedName}
        initialUserRole={resolvedRole}
        initialAvatarUrl={resolvedAvatar}
      />
    </header>
  );
}
