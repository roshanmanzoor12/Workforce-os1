"use client";

import {
  useMemo,
} from "react";

import type {
  WorkspaceRolePublic,
} from "@/types/workspace-roles";


interface CompatibleWorkspaceRole {
  role_key?: string;

  key?: string;

  display_name?: string;

  name?: string;

  is_active?: boolean;

  is_owner_role?: boolean;
}


function getRoleKey(
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


function getRoleName(
  role:
    WorkspaceRolePublic,
): string {
  const compatible =
    role as unknown as
      CompatibleWorkspaceRole;


  return (
    compatible.display_name ??
    compatible.name ??
    getRoleKey(
      role,
    )
  );
}


function canAssign(
  role:
    WorkspaceRolePublic,
): boolean {
  const compatible =
    role as unknown as
      CompatibleWorkspaceRole;


  const key =
    getRoleKey(
      role,
    );


  return (
    (
      compatible.is_active ??
      true
    ) &&
    compatible.is_owner_role !==
      true &&
    key !==
      "owner"
  );
}


export function EmployeeRoleSelect({
  roles,
  value,
  disabled = false,
  onChange,
}: {
  roles:
    WorkspaceRolePublic[];

  value:
    string;

  disabled?:
    boolean;

  onChange:
    (
      roleKey:
        string,
    ) => void;
}) {
  const available =
    useMemo(
      () =>
        roles.filter(
          canAssign,
        ),
      [
        roles,
      ],
    );


  return (
    <label
      style={{
        display:
          "grid",

        gap:
          6,

        fontSize:
          10,
      }}
    >
      Workspace Role

      <select
        value={
          value
        }
        disabled={
          disabled
        }
        onChange={(
          event,
        ) =>
          onChange(
            event.target.value,
          )
        }
        style={{
          width:
            "100%",

          height:
            38,

          padding:
            "0 10px",

          border:
            "1px solid var(--color-border)",

          borderRadius:
            8,

          background:
            "#fffefa",
        }}
      >
        <option value="member">
          Member / Employee
        </option>


        {available.map(
          (
            role,
          ) => {
            const key =
              getRoleKey(
                role,
              );


            if (
              !key ||
              key ===
                "member"
            ) {
              return null;
            }


            return (
              <option
                key={
                  key
                }
                value={
                  key
                }
              >
                {getRoleName(
                  role,
                )}
              </option>
            );
          },
        )}
      </select>
    </label>
  );
}