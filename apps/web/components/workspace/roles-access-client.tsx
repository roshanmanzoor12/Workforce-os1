"use client";

import {
  Plus,
  RefreshCcw,
} from "lucide-react";

import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  PermissionGate,
} from "@/components/workspace/permission-gate";

import {
  RoleEditor,
} from "@/components/workspace/role-editor";

import {
  RoleList,
} from "@/components/workspace/role-list";

import {
  RolePreviewSwitcher,
} from "@/components/workspace/role-preview-switcher";

import {
  WorkspaceMemberList,
} from "@/components/workspace/workspace-member-list";

import {
  WorkspaceRequired,
} from "@/components/workspace/workspace-required";

import {
  useWorkspace,
} from "@/contexts/workspace-context";

import {
  workspaceRolesService,
} from "@/services/workspace-roles.service";

import type {
  WorkspacePermissionDefinition,
} from "@/types/workspace-permissions";

import type {
  WorkspaceRolePublic,
} from "@/types/workspace-roles";


export function RolesAccessClient() {
  return (
    <WorkspaceRequired>
      <RolesAccessContent />
    </WorkspaceRequired>
  );
}


function RolesAccessContent() {
  const {
    workspaceId,

    refreshWorkspaceAccess,
  } =
    useWorkspace();


  const [
    roles,
    setRoles,
  ] =
    useState<
      WorkspaceRolePublic[]
    >([]);


  const [
    catalog,
    setCatalog,
  ] =
    useState<
      WorkspacePermissionDefinition[]
    >([]);


  const [
    selectedRoleId,
    setSelectedRoleId,
  ] =
    useState<
      string | null
    >(null);


  const [
    creating,
    setCreating,
  ] =
    useState(
      false,
    );


  const [
    loading,
    setLoading,
  ] =
    useState(
      true,
    );


  const [
    error,
    setError,
  ] =
    useState<
      string | null
    >(null);


  const load =
    useCallback(
      async () => {
        if (
          !workspaceId
        ) {
          return;
        }


        try {
          setLoading(
            true,
          );

          setError(
            null,
          );


          const [
            roleResponse,

            permissionResponse,
          ] =
            await Promise.all([
              workspaceRolesService.list(
                workspaceId,
              ),

              workspaceRolesService.listPermissions(
                workspaceId,
              ),
            ]);


          setRoles(
            roleResponse.roles,
          );


          setCatalog(
            permissionResponse.permissions,
          );


          setSelectedRoleId(
            (
              previous,
            ) => {
              if (
                previous &&
                roleResponse.roles.some(
                  (
                    role,
                  ) =>
                    role.role_key ===
                    previous,
                )
              ) {
                return previous;
              }


              return (
                roleResponse.roles[0]
                  ?.role_key ??
                null
              );
            },
          );
        } catch (
          cause
        ) {
          setError(
            cause instanceof Error
              ? cause.message
              : "Unable to load roles and permissions.",
          );
        } finally {
          setLoading(
            false,
          );
        }
      },
      [
        workspaceId,
      ],
    );


  useEffect(() => {
    void load();
  }, [
    load,
  ]);


  const selectedRole =
    useMemo(
      () =>
        roles.find(
          (
            role,
          ) =>
            role.role_key ===
            selectedRoleId,
        ) ??
        null,
      [
        roles,

        selectedRoleId,
      ],
    );


  const customRoleCount =
    roles.filter(
      (
        role,
      ) =>
        !role.is_builtin,
    ).length;


  const permissionCount =
    catalog.length;


  function handleSaved(
    role:
      WorkspaceRolePublic,
  ) {
    setRoles(
      (
        previous,
      ) => {
        const exists =
          previous.some(
            (
              item,
            ) =>
              item.role_key ===
              role.role_key,
          );


        if (
          exists
        ) {
          return previous.map(
            (
              item,
            ) =>
              item.role_key ===
              role.role_key
                ? role
                : item,
          );
        }


        return [
          ...previous,

          role,
        ];
      },
    );


    setSelectedRoleId(
      role.role_key,
    );


    setCreating(
      false,
    );


    void refreshWorkspaceAccess();
  }


  function handleDeleted() {
    const remaining =
      roles.filter(
        (
          role,
        ) =>
          role.role_key !==
          selectedRoleId,
      );


    setRoles(
      remaining,
    );


    setSelectedRoleId(
      remaining[0]
        ?.role_key ??
        null,
    );


    setCreating(
      false,
    );


    void refreshWorkspaceAccess();
  }


  if (
    loading
  ) {
    return (
      <div
        className="panel"
        style={{
          padding:
            24,

          textAlign:
            "center",
        }}
      >
        <span className="text-label">
          Loading roles and permissions...
        </span>
      </div>
    );
  }


  return (
    <div
      style={{
        display:
          "grid",

        gap:
          14,
      }}
    >
      <header
        style={{
          display:
            "flex",

          alignItems:
            "flex-start",

          justifyContent:
            "space-between",

          gap:
            15,
        }}
      >
        <div>
          <div className="text-label">
            Settings / Access
          </div>

          <h1
            style={{
              marginTop:
                3,
            }}
          >
            Roles & Permissions
          </h1>

          <p
            className="text-label"
            style={{
              marginTop:
                5,

              maxWidth:
                680,
            }}
          >
            Manage workspace roles, permissions and member access from one place.
          </p>
        </div>


        <div
          style={{
            display:
              "flex",

            gap:
              7,
          }}
        >
          <button
            type="button"
            onClick={() =>
              void load()
            }
            style={
              secondaryButtonStyle
            }
          >
            <RefreshCcw
              size={
                13
              }
            />

            Refresh
          </button>


          <PermissionGate
            permission="roles.manage"
          >
            <button
              type="button"
              onClick={() => {
                setCreating(
                  true,
                );

                setSelectedRoleId(
                  null,
                );
              }}
              style={
                primaryButtonStyle
              }
            >
              <Plus
                size={
                  14
                }
              />

              Create Role
            </button>
          </PermissionGate>
        </div>
      </header>


      {error ? (
        <div
          style={{
            padding:
              10,

            border:
              "1px solid #efc5c5",

            borderRadius:
              7,

            background:
              "#fff5f5",

            color:
              "#a32b2b",

            fontSize:
              10,
          }}
        >
          {error}
        </div>
      ) : null}


      <div
        style={{
          display:
            "grid",

          gridTemplateColumns:
            "repeat(3, minmax(0, 1fr))",

          gap:
            10,
        }}
      >
        <MetricCard
          label="Total Roles"
          value={
            roles.length
          }
        />

        <MetricCard
          label="Custom Roles"
          value={
            customRoleCount
          }
        />

        <MetricCard
          label="Permission Catalog"
          value={
            permissionCount
          }
        />
      </div>


      <RolePreviewSwitcher />


      <div
        style={{
          display:
            "grid",

          gridTemplateColumns:
            "280px minmax(0, 1fr)",

          gap:
            12,

          alignItems:
            "start",
        }}
      >
        <RoleList
          roles={
            roles
          }
          selectedRoleId={
            selectedRoleId
          }
          onSelect={(
            role,
          ) => {
            setCreating(
              false,
            );

            setSelectedRoleId(
              role.role_key,
            );
          }}
        />


        <PermissionGate
          permission="roles.manage"
          fallback={
            <section className="panel">
              <div
                className="panel-body"
                style={{
                  padding:
                    24,

                  textAlign:
                    "center",
                }}
              >
                <h2>
                  Role Management
                </h2>

                <p
                  className="text-label"
                  style={{
                    marginTop:
                      6,
                  }}
                >
                  You can view roles, but you do not have permission to modify them.
                </p>
              </div>
            </section>
          }
        >
          {!creating && selectedRole?.is_builtin ? (
            <section className="panel" style={{ padding: 20 }}>
              <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>
                {selectedRole.display_name} — built-in permissions
              </h2>
              <p style={{ marginBottom: 15, color: "#697586", fontSize: 13 }}>
                This system role has {selectedRole.permissions.length} fixed permissions.
                To customize what a user can access, create a custom role and assign it to that member.
              </p>
              <div style={{ display: "grid", gap: 9, gridTemplateColumns: "repeat(auto-fit,minmax(210px,1fr))" }}>
                {catalog.filter((p) => selectedRole.permissions.includes(p.key)).map((p) => (
                  <div key={p.key} style={{ background: "#fffefa", border: "1px solid #e8e0d3", padding: 10, borderRadius: 8 }}>
                    <strong style={{ fontSize: 12 }}>
                      {p.key}
                    </strong>
                    <div style={{ fontSize: 11, color: "#6b7280" }}>{p.key}</div>
                  </div>
                ))}
              </div>
            </section>
          ) : (
          <RoleEditor
             workspaceId={
              workspaceId ??
              ""
            }
            role={
              creating
                ? null
                : selectedRole
            }
            permissions={
              catalog
            }
            onSaved={
              handleSaved
            }
            onDeleted={
              handleDeleted
            }
            onCancel={
              creating
                ? () =>
                    setCreating(
                      false,
                    )
                : undefined
            }
          />
          )}
        </PermissionGate>
      </div>


      <WorkspaceMemberList
        workspaceId={
          workspaceId ??
          undefined
        }
      />
    </div>
  );
}


function MetricCard({
  label,

  value,
}: {
  label:
    string;

  value:
    number;
}) {
  return (
    <section className="panel">
      <div
        className="panel-body"
        style={{
          padding:
            14,
        }}
      >
        <span className="text-label">
          {label}
        </span>

        <strong
          style={{
            display:
              "block",

            marginTop:
              5,

            fontSize:
              22,
          }}
        >
          {value}
        </strong>
      </div>
    </section>
  );
}


const primaryButtonStyle:
  React.CSSProperties = {
    display:
      "inline-flex",

    alignItems:
      "center",

    gap:
      6,

    padding:
      "8px 12px",

    border:
      "1px solid var(--color-black)",

    borderRadius:
      7,

    background:
      "var(--color-black)",

    color:
      "#fff",

    cursor:
      "pointer",

    fontSize:
      10,
  };


const secondaryButtonStyle:
  React.CSSProperties = {
    display:
      "inline-flex",

    alignItems:
      "center",

    gap:
      6,

    padding:
      "8px 11px",

    border:
      "1px solid var(--color-border)",

    borderRadius:
      7,

    background:
      "#fff",

    cursor:
      "pointer",

    fontSize:
      10,
  };