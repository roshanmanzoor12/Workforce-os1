"use client";

import type {
  ReactNode,
} from "react";

import {
  Building2,
  Check,
  ChevronDown,
  Home,
  Plus,
} from "lucide-react";

import {
  useEffect,
  useRef,
  useState,
} from "react";

import {
  useRouter,
} from "next/navigation";

import {
  useWorkspace,
} from "@/contexts/workspace-context";


export function WorkspaceSwitcher() {
  const router =
    useRouter();


  const rootRef =
    useRef<HTMLDivElement | null>(
      null,
    );


  const [
    open,
    setOpen,
  ] =
    useState(false);


  const {
    mode,

    workspace,

    workspaces,

    membership,

    canCreateWorkspace,

    switchWorkspace,

    enterPersonalMode,
  } =
    useWorkspace();


  const activeMembership =
    workspaces.find(
      (item) =>
        item.membership.status ===
        "active",
    ) ??
    null;


  const businessWorkspace =
    workspace ??
    activeMembership
      ?.workspace ??
    null;


  const businessRole =
    mode === "workspace"
      ? membership
          ?.role_key ??
        activeMembership
          ?.membership
          .role_key ??
        null
      : activeMembership
          ?.membership
          .role_key ??
        null;


  useEffect(() => {
    function handleOutsideClick(
      event: MouseEvent,
    ) {
      if (
        !rootRef.current ||
        rootRef.current.contains(
          event.target as Node,
        )
      ) {
        return;
      }

      setOpen(false);
    }


    document.addEventListener(
      "mousedown",
      handleOutsideClick,
    );


    return () => {
      document.removeEventListener(
        "mousedown",
        handleOutsideClick,
      );
    };
  }, []);


  return (
    <div
      ref={rootRef}
      style={{
        position:
          "relative",
      }}
    >
      <button
        type="button"
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={() =>
          setOpen(
            (current) =>
              !current,
          )
        }
        style={{
          display:
            "flex",

          width: 190,

          height: 36,

          alignItems:
            "center",

          justifyContent:
            "space-between",

          gap: 10,

          padding:
            "0 11px",

          border:
            "1px solid var(--color-border)",

          borderRadius: 8,

          background:
            "#fffefa",

          color:
            "#34373a",

          cursor:
            "pointer",
        }}
      >
        <span
          style={{
            minWidth: 0,

            overflow:
              "hidden",

            whiteSpace:
              "nowrap",

            textOverflow:
              "ellipsis",

            fontSize: 11,

            fontWeight: 500,
          }}
        >
          {mode === "personal"
            ? "Personal"
            : businessWorkspace
                ?.name ??
              "Business Workspace"}
        </span>

        <ChevronDown
          size={13}
          strokeWidth={1.8}
        />
      </button>


      {open ? (
        <div
          role="menu"
          style={{
            position:
              "absolute",

            top: 43,

            right: 0,

            zIndex: 200,

            width: 280,

            overflow:
              "hidden",

            border:
              "1px solid var(--color-border)",

            borderRadius: 10,

            background:
              "#fffefa",

            boxShadow:
              "0 14px 40px rgba(28, 24, 17, .14)",
          }}
        >
          <SwitcherItem
            label="Personal"
            description="Your personal Workforce OS account"
            icon={
              <Home size={15} />
            }
            active={
              mode === "personal"
            }
            onClick={() => {
              setOpen(false);

              enterPersonalMode();
            }}
          />


          <div
            style={{
              height: 1,

              background:
                "var(--color-border)",
            }}
          />


          {businessWorkspace ? (
            <SwitcherItem
              label={
                businessWorkspace.name
              }
              description={
                businessRole
                  ? `${businessRole} access`
                  : "Business workspace"
              }
              icon={
                <Building2
                  size={15}
                />
              }
              active={
                mode === "workspace"
              }
              onClick={() => {
                setOpen(false);

                switchWorkspace(
                  businessWorkspace.id,
                );
              }}
            />
          ) : (
            <div
              style={{
                padding:
                  "14px 12px",

                color:
                  "#7f8286",

                fontSize: 11,
              }}
            >
              No business workspace yet.
            </div>
          )}


          {canCreateWorkspace &&
          !businessWorkspace ? (
            <>
              <div
                style={{
                  height: 1,

                  background:
                    "var(--color-border)",
                }}
              />

              <SwitcherItem
                label="Create workspace"
                description="Start your company workspace"
                icon={
                  <Plus size={15} />
                }
                active={false}
                onClick={() => {
                  setOpen(false);

                  router.push(
                    "/workspaces/new",
                  );
                }}
              />
            </>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}


function SwitcherItem({
  label,
  description,
  icon,
  active,
  onClick,
}: {
  label: string;

  description: string;

  icon: ReactNode;

  active: boolean;

  onClick: () => void;
}) {
  return (
    <button
      type="button"
      role="menuitem"
      onClick={onClick}
      style={{
        display: "flex",

        width: "100%",

        minHeight: 58,

        alignItems:
          "center",

        gap: 10,

        padding:
          "8px 12px",

        border: 0,

        background:
          active
            ? "#f3efe7"
            : "transparent",

        color:
          "#34373a",

        cursor:
          "pointer",

        textAlign:
          "left",
      }}
    >
      <span>
        {icon}
      </span>

      <span
        style={{
          minWidth: 0,

          flex: 1,
        }}
      >
        <strong
          style={{
            display:
              "block",

            overflow:
              "hidden",

            fontSize: 11,

            whiteSpace:
              "nowrap",

            textOverflow:
              "ellipsis",
          }}
        >
          {label}
        </strong>

        <span
          style={{
            display:
              "block",

            marginTop: 2,

            overflow:
              "hidden",

            color:
              "#8a8d91",

            fontSize: 9,

            whiteSpace:
              "nowrap",

            textOverflow:
              "ellipsis",

            textTransform:
              "capitalize",
          }}
        >
          {description}
        </span>
      </span>

      {active ? (
        <Check size={14} />
      ) : null}
    </button>
  );
}