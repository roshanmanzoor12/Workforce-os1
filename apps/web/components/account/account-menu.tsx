"use client";

import {
  ChevronDown,
  Copy,
  LogOut,
  MonitorSmartphone,
  Settings,
  ShieldCheck,
  UserRound,
} from "lucide-react";
import { useRouter } from "next/navigation";
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import { UserAvatar } from "@/components/account/user-avatar";
import { useWorkspace } from "@/contexts/workspace-context";

import {
  authService,
} from "@/services/auth.service";

import type {
  AuthSessionItem,
  AuthUser,
} from "@/types/auth";

interface AccountMenuProps {
  initialUserName?:
    | string
    | null;

  initialUserRole?:
    | string
    | null;

  initialAvatarUrl?:
    | string
    | null;
}

function getUserName(
  user: AuthUser | null,
  fallback?: string | null,
): string {
  if (user) {
    const name = [
      user.first_name,
      user.last_name,
    ]
      .filter(Boolean)
      .join(" ")
      .trim();

    if (name) {
      return name;
    }

    if (user.username) {
      return user.username;
    }

    return user.email;
  }

  return fallback || "Account";
}

export function AccountMenu({
  initialUserName,
  initialUserRole,
  initialAvatarUrl,
}: AccountMenuProps) {
  const router = useRouter();

  const rootRef =
    useRef<HTMLDivElement>(
      null,
    );

  const [open, setOpen] =
    useState(false);

  const { user } = useWorkspace();

  const [
    sessions,
    setSessions,
  ] = useState<
    AuthSessionItem[]
  >([]);

  const [
    loading,
    setLoading,
  ] = useState(false);

  const [
    loggingOut,
    setLoggingOut,
  ] = useState(false);

  const [error, setError] =
    useState<string | null>(
      null,
    );

  const loadAccount =
    useCallback(async () => {
      setLoading(true);
      setError(null);

      try {
        const sessionResponse =
          await authService.getSessions();

        setSessions(
          sessionResponse.sessions,
        );
      } catch (cause) {
        setError(
          cause instanceof Error
            ? cause.message
            : "Unable to load account.",
        );
      } finally {
        setLoading(false);
      }
    }, []);

  useEffect(() => {
    if (open) {
      void loadAccount();
    }
  }, [
    open,
    loadAccount,
  ]);

  useEffect(() => {
    function handleOutside(
      event: MouseEvent,
    ) {
      if (
        rootRef.current &&
        !rootRef.current.contains(
          event.target as Node,
        )
      ) {
        setOpen(false);
      }
    }

    function handleEscape(
      event: KeyboardEvent,
    ) {
      if (
        event.key === "Escape"
      ) {
        setOpen(false);
      }
    }

    document.addEventListener(
      "mousedown",
      handleOutside,
    );

    document.addEventListener(
      "keydown",
      handleEscape,
    );

    return () => {
      document.removeEventListener(
        "mousedown",
        handleOutside,
      );

      document.removeEventListener(
        "keydown",
        handleEscape,
      );
    };
  }, []);

  const displayName =
    useMemo(
      () =>
        getUserName(
          user,
          initialUserName,
        ),
      [
        user,
        initialUserName,
      ],
    );

  const roleLabel =
    initialUserRole ||
    "Member";

  const avatarUrl = user
    ? user.avatar_url
    : initialAvatarUrl ?? null;

  async function copyAccountId() {
    if (!user?.id) {
      return;
    }

    try {
      await navigator.clipboard.writeText(
        user.id,
      );
    } catch {
      // Clipboard access may be
      // unavailable in some contexts.
    }
  }

  async function handleLogout() {
    if (loggingOut) {
      return;
    }

    setLoggingOut(true);

    try {
      await authService.logout();
    } finally {
      router.replace(
        "/login",
      );

      router.refresh();
    }
  }

  async function handleLogoutAll() {
    if (loggingOut) {
      return;
    }

    setLoggingOut(true);

    try {
      await authService.logoutAll();
    } finally {
      router.replace(
        "/login",
      );

      router.refresh();
    }
  }

  return (
    <div
      ref={rootRef}
      style={{
        position: "relative",
      }}
    >
      <button
        type="button"
        aria-label="Open account menu"
        aria-expanded={open}
        onClick={() =>
          setOpen(
            (current) =>
              !current,
          )
        }
        style={{
          display: "flex",
          height: 48,
          minWidth: 165,
          alignItems: "center",
          gap: 10,
          padding:
            "0 14px 0 5px",
          border: 0,
          background:
            "transparent",
          color: "#303235",
          textAlign: "left",
          cursor: "pointer",
        }}
      >
        <span
          style={{
            display: "grid",
            width: 36,
            height: 36,
            flex: "0 0 auto",
            placeItems:
              "center",
            overflow: "hidden",
            borderRadius:
              "50%",
            background:
              "#e9e6df",
            color: "#474a4d",
            fontSize: 11,
            fontWeight: 600,
          }}
        >
          <UserAvatar userId={user?.id} name={displayName} src={avatarUrl} size="100%" />
        </span>

        <span
          style={{
            minWidth: 0,
            flex: 1,
          }}
        >
          <span
            style={{
              display:
                "block",
              overflow:
                "hidden",
              color:
                "#292c2f",
              fontSize: 11,
              fontWeight: 600,
              whiteSpace:
                "nowrap",
              textOverflow:
                "ellipsis",
            }}
          >
            {displayName}
          </span>

          <span
            style={{
              display:
                "block",
              marginTop: 2,
              overflow:
                "hidden",
              color:
                "#7a7e82",
              fontSize: 10,
              whiteSpace:
                "nowrap",
              textOverflow:
                "ellipsis",
              textTransform:
                "capitalize",
            }}
          >
            {roleLabel}
          </span>
        </span>

        <ChevronDown
          size={14}
          strokeWidth={1.7}
          style={{
            transform: open
              ? "rotate(180deg)"
              : undefined,
            transition:
              "transform 150ms ease",
          }}
        />
      </button>

      {open ? (
        <div
          role="menu"
          style={{
            position:
              "absolute",
            top: "calc(100% + 7px)",
            right: 8,
            zIndex: 100,
            width: 300,
            overflow:
              "hidden",
            border:
              "1px solid var(--color-border)",
            borderRadius: 10,
            background:
              "var(--color-surface)",
            boxShadow:
              "0 14px 34px rgba(27, 24, 18, 0.12)",
          }}
        >
          <div
            style={{
              padding: 16,
              borderBottom:
                "1px solid var(--color-border)",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems:
                  "center",
                gap: 11,
              }}
            >
              <span
                style={{
                  display:
                    "grid",
                  width: 42,
                  height: 42,
                  flex:
                    "0 0 auto",
                  placeItems:
                    "center",
                  overflow:
                    "hidden",
                  borderRadius:
                    "50%",
                  background:
                    "#ece9e2",
                  fontWeight:
                    700,
                }}
              >
                <UserAvatar userId={user?.id} name={displayName} src={avatarUrl} size="100%" />
              </span>

              <div
                style={{
                  minWidth: 0,
                }}
              >
                <strong
                  style={{
                    display:
                      "block",
                    overflow:
                      "hidden",
                    fontSize:
                      12,
                    whiteSpace:
                      "nowrap",
                    textOverflow:
                      "ellipsis",
                  }}
                >
                  {displayName}
                </strong>

                <span
                  style={{
                    display:
                      "block",
                    marginTop: 3,
                    overflow:
                      "hidden",
                    color:
                      "var(--color-text-muted)",
                    fontSize:
                      10,
                    whiteSpace:
                      "nowrap",
                    textOverflow:
                      "ellipsis",
                  }}
                >
                  {user?.email ??
                    "Loading account..."}
                </span>
              </div>
            </div>

            {user?.id ? (
              <button
                type="button"
                onClick={() =>
                  void copyAccountId()
                }
                style={{
                  display: "flex",
                  width: "100%",
                  alignItems:
                    "center",
                  justifyContent:
                    "space-between",
                  gap: 10,
                  marginTop: 13,
                  padding:
                    "8px 10px",
                  border:
                    "1px solid var(--color-border)",
                  borderRadius:
                    7,
                  background:
                    "var(--color-app-background)",
                  cursor:
                    "pointer",
                }}
              >
                <span
                  style={{
                    minWidth:
                      0,
                    overflow:
                      "hidden",
                    fontSize:
                      9,
                    whiteSpace:
                      "nowrap",
                    textOverflow:
                      "ellipsis",
                  }}
                >
                  ID: {user.id}
                </span>

                <Copy
                  size={13}
                />
              </button>
            ) : null}
          </div>

          {error ? (
            <div
              style={{
                margin:
                  "10px 12px 0",
                padding: 9,
                borderRadius:
                  6,
                background:
                  "var(--color-danger-soft)",
                color:
                  "var(--color-danger)",
                fontSize: 10,
              }}
            >
              {error}
            </div>
          ) : null}

          <MenuButton
            icon={
              <UserRound
                size={15}
              />
            }
            label="Account Settings"
            onClick={() => {
              setOpen(false);

              router.push(
                "/settings/account",
              );
            }}
          />

          <MenuButton
            icon={
              <ShieldCheck
                size={15}
              />
            }
            label="Security & Sessions"
            meta={
              loading
                ? "..."
                : String(
                    sessions.length,
                  )
            }
            onClick={() => {
              setOpen(false);

              router.push(
                "/settings/security",
              );
            }}
          />

          <MenuButton
            icon={
              <Settings
                size={15}
              />
            }
            label="Settings"
            onClick={() => {
              setOpen(false);

              router.push(
                "/settings",
              );
            }}
          />

          <div
            style={{
              borderTop:
                "1px solid var(--color-border)",
            }}
          >
            <MenuButton
              icon={
                <MonitorSmartphone
                  size={15}
                />
              }
              label="Sign out all devices"
              disabled={
                loggingOut
              }
              onClick={() =>
                void handleLogoutAll()
              }
            />

            <MenuButton
              icon={
                <LogOut
                  size={15}
                />
              }
              label={
                loggingOut
                  ? "Signing out..."
                  : "Sign out"
              }
              danger
              disabled={
                loggingOut
              }
              onClick={() =>
                void handleLogout()
              }
            />
          </div>
        </div>
      ) : null}
    </div>
  );
}

function MenuButton({
  icon,
  label,
  meta,
  danger = false,
  disabled = false,
  onClick,
}: {
  icon: React.ReactNode;
  label: string;
  meta?: string;
  danger?: boolean;
  disabled?: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      role="menuitem"
      disabled={disabled}
      onClick={onClick}
      style={{
        display: "flex",
        width: "100%",
        minHeight: 42,
        alignItems: "center",
        gap: 10,
        padding: "0 14px",
        border: 0,
        background:
          "transparent",
        color: danger
          ? "var(--color-danger)"
          : "#333639",
        fontSize: 11,
        textAlign: "left",
        cursor: disabled
          ? "not-allowed"
          : "pointer",
        opacity: disabled
          ? 0.6
          : 1,
      }}
    >
      {icon}

      <span
        style={{
          flex: 1,
        }}
      >
        {label}
      </span>

      {meta ? (
        <span
          style={{
            color:
              "var(--color-text-muted)",
            fontSize: 10,
          }}
        >
          {meta}
        </span>
      ) : null}
    </button>
  );
}