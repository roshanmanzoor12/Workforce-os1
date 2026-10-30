"use client";

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
import { workspaceLogoSrc } from "@/lib/workspace/logo-url";

export function WorkspaceSwitcher() {
  const router =
    useRouter();

  const wrapperRef =
    useRef<HTMLDivElement | null>(
      null,
    );

  const [
    open,
    setOpen,
  ] =
    useState(
      false,
    );

  const {
    mode,
    workspace,
    workspaces,
    workspaceAccess,
    switchWorkspace,
    enterPersonalMode,
  } =
    useWorkspace();

  useEffect(() => {
    function handleClick(
      event:
        MouseEvent,
    ) {
      if (
        !wrapperRef.current
      ) {
        return;
      }

      if (
        !wrapperRef.current.contains(
          event.target as Node,
        )
      ) {
        setOpen(
          false,
        );
      }
    }

    document.addEventListener(
      "mousedown",
      handleClick,
    );

    return () => {
      document.removeEventListener(
        "mousedown",
        handleClick,
      );
    };
  }, []);

  return (
    <div
      ref={
        wrapperRef
      }
      style={{
        position:
          "relative",
      }}
    >
      <button
        type="button"
        aria-expanded={
          open
        }
        aria-haspopup="menu"
        onClick={() =>
          setOpen(
            (value) =>
              !value,
          )
        }
        style={{
          display:
            "flex",
          width:
            190,
          height:
            36,
          alignItems:
            "center",
          justifyContent:
            "space-between",
          gap:
            10,
          padding:
            "0 11px",
          border: mode === "workspace" ? `1px solid ${workspace?.accent_color ?? "#F59E0B"}` : "1px solid var(--color-border)",
          borderRadius:
            8,
          background:
            "#fffefa",
          color:
            "#34373a",
          cursor:
            "pointer",
        }}
      >
        {mode === "workspace" ? (
          <span aria-hidden="true" style={{ width: 22, height: 22, borderRadius: 6, flexShrink: 0, display: "grid", placeItems: "center", overflow: "hidden", backgroundColor: workspace?.primary_color ?? "#2563EB", color: "#fff", fontSize: 10, fontWeight: 700 }}>
            {workspace?.logo_url ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={workspaceLogoSrc(workspace.logo_url)} alt="" style={{ width: "100%", height: "100%", objectFit: "cover" }} />
            ) : workspace?.name?.trim().slice(0, 2).toUpperCase() ?? "WS"}
          </span>
        ) : null}
        <span
          style={{
            overflow:
              "hidden",
            whiteSpace:
              "nowrap",
            textOverflow:
              "ellipsis",
            fontSize:
              11,
            fontWeight:
              500,
          }}
        >
          {mode ===
          "personal"
            ? "Personal"
            : workspace?.name ??
              "Workspace"}
        </span>

        <ChevronDown
          size={13}
        />
      </button>

      {open ? (
        <div
          role="menu"
          style={{
            position:
              "absolute",
            top:
              43,
            right:
              0,
            zIndex:
              100,
            width:
              270,
            overflow:
              "hidden",
            border:
              "1px solid var(--color-border)",
            borderRadius:
              10,
            background:
              "#fffefa",
            boxShadow:
              "0 12px 36px rgba(24,20,12,.12)",
          }}
        >
          <SwitcherItem
            icon={
              <Home
                size={15}
              />
            }
            label="Personal"
            active={
              mode ===
              "personal"
            }
            onClick={() => {
              setOpen(
                false,
              );

              enterPersonalMode();
            }}
          />

          <div
            style={{
              height:
                1,
              background:
                "var(--color-border)",
            }}
          />

          <div
            style={{
              padding:
                "9px 11px 5px",
              color:
                "#8a8d91",
              fontSize:
                9,
              fontWeight:
                600,
              textTransform:
                "uppercase",
              letterSpacing:
                ".08em",
            }}
          >
            Workspaces
          </div>

          {workspaces.length ===
          0 ? (
            <div
              className="text-label"
              style={{
                padding:
                  "10px 12px 14px",
              }}
            >
              No workspaces yet
            </div>
          ) : (
            workspaces.map(
              (item) => (
                <SwitcherItem
                  key={
                    item.workspace.id
                  }
                  icon={
                    <Building2
                      size={15}
                    />
                  }
                  label={
                    item.workspace.name
                  }
                  active={
                    mode ===
                      "workspace" &&
                    workspace?.id ===
                      item.workspace.id
                  }
                  onClick={() => {
                    setOpen(
                      false,
                    );

                    switchWorkspace(
                      item.workspace.id,
                    );
                  }}
                />
              ),
            )
          )}

          <div
            style={{
              height:
                1,
              marginTop:
                5,
              background:
                "var(--color-border)",
            }}
          />

          {workspaceAccess
            ?.allowed ? (
            <SwitcherItem
              icon={
                <Plus
                  size={15}
                />
              }
              label="Create workspace"
              active={
                false
              }
              onClick={() => {
                setOpen(
                  false,
                );

                router.push(
                  "/workspaces/new",
                );
              }}
            />
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

function SwitcherItem({
  icon,
  label,
  active,
  onClick,
}: {
  icon:
    React.ReactNode;

  label:
    string;

  active:
    boolean;

  onClick:
    () => void;
}) {
  return (
    <button
      type="button"
      role="menuitem"
      onClick={
        onClick
      }
      style={{
        display:
          "flex",
        width:
          "100%",
        minHeight:
          40,
        alignItems:
          "center",
        gap:
          10,
        padding:
          "0 12px",
        border:
          0,
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
      {icon}

      <span
        style={{
          minWidth:
            0,
          flex:
            1,
          overflow:
            "hidden",
          whiteSpace:
            "nowrap",
          textOverflow:
            "ellipsis",
          fontSize:
            11,
        }}
      >
        {label}
      </span>

      {active ? (
        <Check
          size={14}
        />
      ) : null}
    </button>
  );
}