"use client";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";

import { usePathname } from "next/navigation";
import { Menu, X } from "lucide-react";

import { AppHeader } from "./app-header";
import { AppSidebar } from "./app-sidebar";
import { WorkspaceBillingBoundary } from "@/components/workspace/workspace-billing-boundary";

import { useModalFocus } from "@/lib/ui/use-modal-focus";

import styles from "./workspace-shell.module.css";

interface WorkspaceShellProps {
  children: ReactNode;

  workspaceName?: string | null;

  userName?: string | null;
  userRole?: string | null;
  avatarUrl?: string | null;
  notificationCount?: number;

  systemOperational?: boolean;
  lastSyncedLabel?: string | null;
  activeSessions?: number | null;
  serverTimeLabel?: string | null;
  summaryLabel?: string | null;
}

export function WorkspaceShell({
  children,
  workspaceName,
  userName,
  userRole,
  avatarUrl,
  notificationCount = 0,
}: WorkspaceShellProps) {
  const pathname = usePathname();

  const [mobileSidebarOpen, setMobileSidebarOpen] =
    useState(false);

  const [isMobile, setIsMobile] = useState(false);

  const mainRef = useRef<HTMLDivElement>(null);

  const closeMobileSidebar = useCallback(() => {
    setMobileSidebarOpen(false);
  }, []);

  const drawerOpen = isMobile && mobileSidebarOpen;

  useEffect(() => {
    const media = window.matchMedia(
      "(max-width: 1023px)",
    );

    function updateViewport() {
      setIsMobile(media.matches);

      if (!media.matches) {
        setMobileSidebarOpen(false);
      }
    }

    updateViewport();

    media.addEventListener(
      "change",
      updateViewport,
    );

    return () => {
      media.removeEventListener(
        "change",
        updateViewport,
      );
    };
  }, []);

  useEffect(() => {
    closeMobileSidebar();
  }, [
    pathname,
    workspaceName,
    closeMobileSidebar,
  ]);

  useEffect(() => {
    if (!drawerOpen) return;

    const main = mainRef.current;
    const oldOverflow = document.body.style.overflow;
    const oldInert = main?.inert ?? false;

    document.body.style.overflow = "hidden";

    if (main) {
      main.inert = true;
    }

    return () => {
      document.body.style.overflow = oldOverflow;

      if (main) {
        main.inert = oldInert;
      }
    };
  }, [drawerOpen]);

  const sidebarRef = useModalFocus(
    drawerOpen,
    closeMobileSidebar,
  );

  return (
    <div className={styles.shell}>
      <div
        id="workforce-workspace-navigation"
        ref={sidebarRef}
        tabIndex={-1}
        className={styles.sidebar}
        data-open={drawerOpen ? "true" : "false"}
        role={drawerOpen ? "dialog" : undefined}
        aria-modal={drawerOpen ? true : undefined}
        aria-label="Workspace navigation"
        aria-hidden={
          isMobile && !drawerOpen
            ? true
            : undefined
        }
        onClick={(event) => {
          if (
            drawerOpen &&
            event.target instanceof Element &&
            event.target.closest("a[href]")
          ) {
            closeMobileSidebar();
          }
        }}
      >
        <div className={styles.drawerHeader}>
          <strong>Navigation</strong>

          <button
            type="button"
            className={styles.iconButton}
            onClick={closeMobileSidebar}
            aria-label="Close navigation"
          >
            <X size={20} />
          </button>
        </div>

        <AppSidebar
          workspaceName={workspaceName}
        />
      </div>

      {drawerOpen ? (
        <button
          type="button"
          className={styles.overlay}
          tabIndex={-1}
          onClick={closeMobileSidebar}
          aria-label="Close navigation"
        />
      ) : null}

      <div
        ref={mainRef}
        className={styles.main}
      >
        <div className={styles.headerRow}>
          <button
            type="button"
            className={`${styles.iconButton} ${styles.mobileMenuButton}`}
            onClick={() =>
              setMobileSidebarOpen(
                (open) => !open,
              )
            }
            aria-label="Open navigation"
            aria-controls="workforce-workspace-navigation"
            aria-expanded={drawerOpen}
          >
            <Menu size={20} />
          </button>

          <div className={styles.headerContent}>
            <AppHeader
              workspaceName={workspaceName}
              userName={userName}
              userRole={userRole}
              avatarUrl={avatarUrl}
              notificationCount={notificationCount}
            />
          </div>
        </div>

        <main
          id="main-content"
          className={styles.content}
        >
          <WorkspaceBillingBoundary>
            {children}
          </WorkspaceBillingBoundary>
        </main>

      </div>
    </div>
  );
}
