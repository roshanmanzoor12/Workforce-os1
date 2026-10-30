"use client";

import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  AlertTriangle,
  Check,
  Loader2,
  Trash2,
  X,
} from "lucide-react";

import {
  workspaceRolesService,
} from "@/services/workspace-roles.service";

import type {
  WorkspacePermissionDefinition,
} from "@/types/workspace-permissions";

import type {
  WorkspaceRolePublic,
} from "@/types/workspace-roles";


interface RoleEditorProps {
  workspaceId:
    string;

  role?:
    WorkspaceRolePublic | null;

  permissions:
    WorkspacePermissionDefinition[];

  onSaved?:
    (
      role:
        WorkspaceRolePublic,
    ) => void;

  onDeleted?:
    () => void;

  onCancel?:
    () => void;
}


export function RoleEditor({
  workspaceId,

  role = null,

  permissions,

  onSaved,

  onDeleted,

  onCancel,
}: RoleEditorProps) {
  const editing =
    Boolean(
      role,
    );


  const [
    roleKey,
    setRoleKey,
  ] =
    useState(
      role?.role_key ??
      "",
    );


  const [
    displayName,
    setDisplayName,
  ] =
    useState(
      role?.display_name ??
      "",
    );


  const [
    description,
    setDescription,
  ] =
    useState(
      role?.description ??
      "",
    );


  const [
    selectedPermissions,
    setSelectedPermissions,
  ] =
    useState<
      Set<string>
    >(
      new Set(
        role?.permissions ??
          [],
      ),
    );


  const [
    isActive,
    setIsActive,
  ] =
    useState(
      role?.is_active ??
      true,
    );


  const [
    saving,
    setSaving,
  ] =
    useState(
      false,
    );


  const [
    deleting,
    setDeleting,
  ] =
    useState(
      false,
    );


  const [
    error,
    setError,
  ] =
    useState<
      string | null
    >(null);


  useEffect(() => {
    setRoleKey(
      role?.role_key ??
        "",
    );

    setDisplayName(
      role?.display_name ??
        "",
    );

    setDescription(
      role?.description ??
        "",
    );

    setSelectedPermissions(
      new Set(
        role?.permissions ??
          [],
      ),
    );

    setIsActive(
      role?.is_active ??
        true,
    );
  }, [
    role,
  ]);


  const groups =
    useMemo(() => {
      const map =
        new Map<
          string,
          WorkspacePermissionDefinition[]
        >();


      for (
        const permission
        of permissions
      ) {
        const existing =
          map.get(
            permission.group,
          ) ??
          [];

        existing.push(
          permission,
        );

        map.set(
          permission.group,
          existing,
        );
      }


      return Array.from(
        map.entries(),
      );
    }, [
      permissions,
    ]);


  function togglePermission(
    key:
      string,
  ) {
    setSelectedPermissions(
      (
        previous,
      ) => {
        const next =
          new Set(
            previous,
          );


        if (
          next.has(
            key,
          )
        ) {
          next.delete(
            key,
          );
        } else {
          next.add(
            key,
          );
        }


        return next;
      },
    );
  }


  function toggleGroup(
    groupPermissions:
      WorkspacePermissionDefinition[],
  ) {
    const keys =
      groupPermissions.map(
        (
          permission,
        ) =>
          permission.key,
      );


    const allSelected =
      keys.every(
        (
          key,
        ) =>
          selectedPermissions.has(
            key,
          ),
      );


    setSelectedPermissions(
      (
        previous,
      ) => {
        const next =
          new Set(
            previous,
          );


        for (
          const key
          of keys
        ) {
          if (
            allSelected
          ) {
            next.delete(
              key,
            );
          } else {
            next.add(
              key,
            );
          }
        }


        return next;
      },
    );
  }


  async function submit(
    event:
      React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();


    if (
      !workspaceId
    ) {
      return;
    }

    if (role?.is_builtin) {
      setError("Built-in roles are managed by the system. Create a custom role to choose permissions.");
      return;
    }


    const cleanName =
      displayName.trim();


    if (
      !cleanName
    ) {
      setError(
        "Role display name is required.",
      );

      return;
    }


    if (
      !editing &&
      !roleKey.trim()
    ) {
      setError(
        "Role key is required.",
      );

      return;
    }


    try {
      setSaving(
        true,
      );

      setError(
        null,
      );


      if (editing && role && (role.id || role.is_builtin)) {
        const updated =
          await (role.is_builtin
            ? workspaceRolesService.updateBuiltin(workspaceId, role.role_key, {
                permissions: Array.from(selectedPermissions),
              })
            : workspaceRolesService.update(workspaceId, role.id!, {
              display_name:
                cleanName,

              description:
                description.trim() ||
                null,

              permissions:
                Array.from(
                  selectedPermissions,
                ),

              is_active:
                isActive,
            },
          ));


        onSaved?.(
          updated,
        );

        return;
      }


      const created =
        await workspaceRolesService.create(
          workspaceId,
          {
            role_key:
              roleKey
                .trim()
                .toLowerCase()
                .replace(
                  /[^a-z0-9._-]+/g,
                  "_",
                ),

            display_name:
              cleanName,

            description:
              description.trim() ||
              null,

            permissions:
              Array.from(
                selectedPermissions,
              ),
          },
        );


      onSaved?.(
        created,
      );
    } catch (
      cause
    ) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Unable to save role.",
      );
    } finally {
      setSaving(
        false,
      );
    }
  }


  async function removeRole() {
    if (
      !role?.id ||
      role.is_builtin ||
      role.is_immutable
    ) {
      return;
    }


    if (
      !window.confirm(
        `Delete "${role.display_name}"?`,
      )
    ) {
      return;
    }


    try {
      setDeleting(
        true,
      );

      setError(
        null,
      );


      await workspaceRolesService.remove(
        workspaceId,
        role.id,
      );


      onDeleted?.();
    } catch (
      cause
    ) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Unable to delete role.",
      );
    } finally {
      setDeleting(
        false,
      );
    }
  }


  return (
    <form
      onSubmit={
        submit
      }
      className="panel"
    >
      <div
        className="panel-body"
        style={{
          display:
            "grid",

          gap:
            18,

          padding:
            18,
        }}
      >
        <div
          style={{
            display:
              "flex",

            justifyContent:
              "space-between",

            gap:
              12,
          }}
        >
          <div>
            <h2>
              {editing
                ? "Edit Role"
                : "Create Role"}
            </h2>

            <p className="text-label">
              Configure role information and workspace permissions.
            </p>
          </div>

          {onCancel ? (
            <button
              type="button"
              onClick={
                onCancel
              }
              style={{
                border:
                  "1px solid var(--color-border)",

                borderRadius:
                  7,

                background:
                  "#fff",

                padding:
                  8,

                cursor:
                  "pointer",
              }}
            >
              <X
                size={
                  15
                }
              />
            </button>
          ) : null}
        </div>


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
              "repeat(auto-fit, minmax(220px, 1fr))",

            gap:
              12,
          }}
        >
          <label>
            <span className="text-label">
              Role Key
            </span>

            <input
              value={
                roleKey
              }
              onChange={(
                event,
              ) =>
                setRoleKey(
                  event.target.value,
                )
              }
              disabled={
                editing
              }
              placeholder="sales_manager"
              style={{
                width:
                  "100%",

                marginTop:
                  5,

                padding:
                  "9px 10px",

                border:
                  "1px solid var(--color-border)",

                borderRadius:
                  7,
              }}
            />
          </label>


          <label>
            <span className="text-label">
              Display Name
            </span>

            <input
              value={
                displayName
              }
              onChange={(
                event,
              ) =>
                setDisplayName(
                  event.target.value,
                )
              }
              placeholder="Sales Manager"
              style={{
                width:
                  "100%",

                marginTop:
                  5,

                padding:
                  "9px 10px",

                border:
                  "1px solid var(--color-border)",

                borderRadius:
                  7,
              }}
            />
          </label>
        </div>


        <label>
          <span className="text-label">
            Description
          </span>

          <textarea
            value={
              description
            }
            onChange={(
              event,
            ) =>
              setDescription(
                event.target.value,
              )
            }
            rows={
              3
            }
            placeholder="Describe what this role is allowed to do."
            style={{
              width:
                "100%",

              marginTop:
                5,

              padding:
                "9px 10px",

              border:
                "1px solid var(--color-border)",

              borderRadius:
                7,

              resize:
                "vertical",
            }}
          />
        </label>


        {editing &&
        role?.is_immutable ? (
          <div
            style={{
              display:
                "flex",

              alignItems:
                "center",

              gap:
                7,

              padding:
                10,

              border:
                "1px solid #e5d7a8",

              borderRadius:
                7,

              background:
                "#fffaf0",

              fontSize:
                10,
            }}
          >
            <AlertTriangle
              size={
                14
              }
            />

            This is a built-in immutable role.
          </div>
        ) : null}


        <div>
          <div
            style={{
              display:
                "flex",

              justifyContent:
                "space-between",

              alignItems:
                "center",

              marginBottom:
                10,
            }}
          >
            <div>
              <strong>
                Permissions
              </strong>

              <div className="text-label">
                {
                  selectedPermissions.size
                }{" "}
                selected
              </div>
            </div>
          </div>


          <div
            style={{
              display:
                "grid",

              gap:
                10,
            }}
          >
            {groups.map(
              ([
                group,
                groupPermissions,
              ]) => {
                const allSelected =
                  groupPermissions.every(
                    (
                      permission,
                    ) =>
                      selectedPermissions.has(
                        permission.key,
                      ),
                  );


                return (
                  <section
                    key={
                      group
                    }
                    style={{
                      border:
                        "1px solid var(--color-border)",

                      borderRadius:
                        8,

                      overflow:
                        "hidden",
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

                        padding:
                          "9px 11px",

                        background:
                          "#faf8f1",
                      }}
                    >
                      <strong
                        style={{
                          fontSize:
                            11,
                        }}
                      >
                        {
                          group
                        }
                      </strong>

                      <button
                        type="button"
                        onClick={() =>
                          toggleGroup(
                            groupPermissions,
                          )
                        }
                        style={{
                          border:
                            "none",

                          background:
                            "transparent",

                          cursor:
                            "pointer",

                          fontSize:
                            10,
                        }}
                      >
                        {allSelected
                          ? "Clear group"
                          : "Select group"}
                      </button>
                    </div>


                    <div
                      style={{
                        display:
                          "grid",

                        gridTemplateColumns:
                          "repeat(auto-fit, minmax(230px, 1fr))",

                        gap:
                          8,

                        padding:
                          10,
                      }}
                    >
                      {groupPermissions.map(
                        (
                          permission,
                        ) => {
                          const checked =
                            selectedPermissions.has(
                              permission.key,
                            );


                          return (
                            <label
                              key={
                                permission.key
                              }
                              style={{
                                display:
                                  "flex",

                                alignItems:
                                  "flex-start",

                                gap:
                                  8,

                                padding:
                                  9,

                                border:
                                  "1px solid var(--color-border)",

                                borderRadius:
                                  7,

                                cursor:
                                  "pointer",
                              }}
                            >
                              <input
                                type="checkbox"
                                checked={
                                  checked
                                }
                                onChange={() =>
                                  togglePermission(
                                    permission.key,
                                  )
                                }
                                style={{
                                  marginTop:
                                    2,
                                }}
                              />

                              <span>
                                <strong
                                  style={{
                                    display:
                                      "block",

                                    fontSize:
                                      10,
                                  }}
                                >
                                  {
                                    permission.display_name
                                  }
                                </strong>

                                <span
                                  className="text-label"
                                  style={{
                                    display:
                                      "block",

                                    marginTop:
                                      3,
                                  }}
                                >
                                  {
                                    permission.description
                                  }
                                </span>
                              </span>
                            </label>
                          );
                        },
                      )}
                    </div>
                  </section>
                );
              },
            )}
          </div>
        </div>


        {editing ? (
          <label
            style={{
              display:
                "flex",

              alignItems:
                "center",

              gap:
                8,
            }}
          >
            <input
              type="checkbox"
              checked={
                isActive
              }
              onChange={(
                event,
              ) =>
                setIsActive(
                  event.target.checked,
                )
              }
              disabled={
                role?.is_immutable
              }
            />

            <span>
              Active role
            </span>
          </label>
        ) : null}


        <div
          style={{
            display:
              "flex",

            justifyContent:
              "space-between",

            alignItems:
              "center",

            gap:
              10,

            paddingTop:
              4,
          }}
        >
          <div>
            {editing &&
            role &&
            !role.is_builtin &&
            !role.is_immutable ? (
              <button
                type="button"
                onClick={
                  removeRole
                }
                disabled={
                  deleting ||
                  saving
                }
                style={{
                  display:
                    "inline-flex",

                  alignItems:
                    "center",

                  gap:
                    6,

                  padding:
                    "8px 11px",

                  border:
                    "1px solid #e5bebe",

                  borderRadius:
                    7,

                  background:
                    "#fff",

                  color:
                    "#a32b2b",

                  cursor:
                    "pointer",
                }}
              >
                {deleting ? (
                  <Loader2
                    size={
                      13
                    }
                  />
                ) : (
                  <Trash2
                    size={
                      13
                    }
                  />
                )}

                Delete Role
              </button>
            ) : null}
          </div>


          <button
            type="submit"
            disabled={
              saving ||
              deleting ||
              Boolean(role?.is_builtin)
            }
            style={{
              display:
                "inline-flex",

              alignItems:
                "center",

              gap:
                6,

              padding:
                "9px 13px",

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
            }}
          >
            {saving ? (
              <Loader2
                size={
                  14
                }
              />
            ) : (
              <Check
                size={
                  14
                }
              />
            )}

            {editing
              ? "Save Changes"
              : "Create Role"}
          </button>
        </div>
      </div>
    </form>
  );
}