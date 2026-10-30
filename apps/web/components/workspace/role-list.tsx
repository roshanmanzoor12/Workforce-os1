"use client";

import {
  Pencil,
  ShieldCheck,
} from "lucide-react";

import type {
  WorkspaceRolePublic,
} from "@/types/workspace-roles";


interface RoleListProps {
  roles:
    WorkspaceRolePublic[];

  selectedRoleId:
    string | null;

  onSelect:
    (
      role:
        WorkspaceRolePublic,
    ) => void;
}


export function RoleList({
  roles,

  selectedRoleId,

  onSelect,
}: RoleListProps) {
  return (
    <section className="panel">
      <div
        className="panel-body"
        style={{
          padding:
            14,
        }}
      >
        <div
          style={{
            marginBottom:
              10,
          }}
        >
          <h2>
            Roles
          </h2>

          <p className="text-label">
            Built-in and custom workspace roles.
          </p>
        </div>


        <div
          style={{
            display:
              "grid",

            gap:
              7,
          }}
        >
          {roles.map(
            (
              role,
            ) => {
              const selected =
                selectedRoleId ===
                role.role_key;


              return (
                <button
                  key={
                    role.id ??
                    role.role_key
                  }
                  type="button"
                  onClick={() =>
                    onSelect(
                      role,
                    )
                  }
                  style={{
                    width:
                      "100%",

                    padding:
                      10,

                    border:
                      selected
                        ? "1px solid var(--color-black)"
                        : "1px solid var(--color-border)",

                    borderRadius:
                      7,

                    background:
                      selected
                        ? "#faf7ed"
                        : "#fff",

                    textAlign:
                      "left",

                    cursor:
                      "pointer",
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
                        8,
                    }}
                  >
                    <div
                      style={{
                        display:
                          "flex",

                        alignItems:
                          "center",

                        gap:
                          7,
                      }}
                    >
                      {role.is_builtin ? (
                        <ShieldCheck
                          size={
                            14
                          }
                        />
                      ) : (
                        <Pencil
                          size={
                            13
                          }
                        />
                      )}

                      <strong
                        style={{
                          fontSize:
                            11,
                        }}
                      >
                        {
                          role.display_name
                        }
                      </strong>
                    </div>


                    <span
                      style={{
                        fontSize:
                          8,

                        padding:
                          "3px 5px",

                        borderRadius:
                          4,

                        border:
                          "1px solid var(--color-border)",
                      }}
                    >
                      {role.is_builtin
                        ? "Built-in"
                        : "Custom"}
                    </span>
                  </div>


                  <div
                    className="text-label"
                    style={{
                      marginTop:
                        5,
                    }}
                  >
                    {
                      role.description ||
                      role.role_key
                    }
                  </div>


                  <div
                    className="text-label"
                    style={{
                      marginTop:
                        6,
                    }}
                  >
                    {
                      role.permissions
                        ?.length ??
                      0
                    }{" "}
                    permissions
                  </div>
                </button>
              );
            },
          )}
        </div>
      </div>
    </section>
  );
}