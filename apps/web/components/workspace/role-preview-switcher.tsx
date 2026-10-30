"use client";

import {
  Eye,
  RotateCcw,
} from "lucide-react";

import type {
  WorkspaceNavigationView,
} from "@/types/workspace-access";

import {
  useWorkspace,
} from "@/contexts/workspace-context";


const PREVIEW_OPTIONS:
  {
    value:
      WorkspaceNavigationView;

    label:
      string;

    description:
      string;
  }[] = [
    {
      value:
        "owner",

      label:
        "Owner",

      description:
        "Full workspace access",
    },

    {
      value:
        "admin",

      label:
        "Admin",

      description:
        "Administrative workspace access",
    },

    {
      value:
        "manager",

      label:
        "Manager",

      description:
        "Team-level access",
    },

    {
      value:
        "member",

      label:
        "Member",

      description:
        "Employee-level access",
    },

    {
      value:
        "client",

      label:
        "Client",

      description:
        "Client / guest access",
    },
  ];


export function RolePreviewSwitcher() {
  const {
    navigationView,

    effectiveNavigationView,

    previewNavigationView,

    setRolePreview,

    clearRolePreview,
  } =
    useWorkspace();


  if (
    navigationView !==
    "owner"
  ) {
    return null;
  }


  const activeView =
    previewNavigationView ??
    effectiveNavigationView;


  return (
    <section
      className="panel"
      style={{
        border:
          "1px solid var(--color-border)",
      }}
    >
      <div
        className="panel-body"
        style={{
          padding:
            14,
        }}
      >
        <div
          style={{
            display:
              "flex",

            alignItems:
              "center",

            justifyContent:
              "space-between",

            gap:
              12,

            marginBottom:
              12,
          }}
        >
          <div
            style={{
              display:
                "flex",

              alignItems:
                "center",

              gap:
                8,
            }}
          >
            <Eye
              size={
                16
              }
            />

            <div>
              <strong>
                Role Preview
              </strong>

              <div className="text-label">
                Preview the workspace as another role.
              </div>
            </div>
          </div>


          {previewNavigationView ? (
            <button
              type="button"
              onClick={
                clearRolePreview
              }
              style={{
                display:
                  "inline-flex",

                alignItems:
                  "center",

                gap:
                  6,

                border:
                  "1px solid var(--color-border)",

                borderRadius:
                  7,

                background:
                  "#fff",

                padding:
                  "7px 10px",

                cursor:
                  "pointer",
              }}
            >
              <RotateCcw
                size={
                  13
                }
              />

              Exit Preview
            </button>
          ) : null}
        </div>


        <div
          style={{
            display:
              "grid",

            gridTemplateColumns:
              "repeat(auto-fit, minmax(150px, 1fr))",

            gap:
              8,
          }}
        >
          {PREVIEW_OPTIONS.map(
            (
              option,
            ) => {
              const active =
                activeView ===
                option.value;

              return (
                <button
                  key={
                    option.value
                  }
                  type="button"
                  onClick={() =>
                    setRolePreview(
                      option.value,
                    )
                  }
                  style={{
                    textAlign:
                      "left",

                    padding:
                      11,

                    border:
                      active
                        ? "1px solid var(--color-black)"
                        : "1px solid var(--color-border)",

                    borderRadius:
                      7,

                    background:
                      active
                        ? "#f7f4eb"
                        : "#fff",

                    cursor:
                      "pointer",
                  }}
                >
                  <strong
                    style={{
                      display:
                        "block",

                      fontSize:
                        11,
                    }}
                  >
                    {option.label}
                  </strong>

                  <span
                    className="text-label"
                    style={{
                      display:
                        "block",

                      marginTop:
                        4,
                    }}
                  >
                    {
                      option.description
                    }
                  </span>
                </button>
              );
            },
          )}
        </div>
      </div>
    </section>
  );
}