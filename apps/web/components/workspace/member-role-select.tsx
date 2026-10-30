"use client";

import {
  useEffect,
  useState,
} from "react";

import {
  Loader2,
} from "lucide-react";

import {
  useWorkspace,
} from "@/contexts/workspace-context";

import {
  hasPermission,
} from "@/lib/workspace/access";

import {
  workspaceMembersService,
} from "@/services/workspace-members.service";


interface MemberRoleSelectProps {
  membershipId:
    string;

  value:
    string;

  disabled?:
    boolean;

  onSaved?:
    (
      roleKey:
        string,
    ) => void;
}


export function MemberRoleSelect({
  membershipId,

  value,

  disabled = false,

  onSaved,
}: MemberRoleSelectProps) {
  const {
    workspaceId,

    availableRoles,

    effectivePermissions,

    effectiveNavigationView,
  } =
    useWorkspace();


  const [
    selectedRole,
    setSelectedRole,
  ] =
    useState(
      value,
    );


  const [
    saving,
    setSaving,
  ] =
    useState(false);


  const [
    error,
    setError,
  ] =
    useState<
      string | null
    >(null);


  useEffect(() => {
    setSelectedRole(
      value,
    );
  }, [
    value,
  ]);


  const canAssign =
    hasPermission(
      effectivePermissions,
      "roles.assign",
      effectiveNavigationView,
    );


  async function save(
    nextRole:
      string,
  ) {
    if (
      !workspaceId ||
      !nextRole ||
      nextRole ===
        value
    ) {
      return;
    }


    try {
      setSaving(
        true,
      );

      setError(
        null,
      );


      await workspaceMembersService.updateRole(
        workspaceId,
        membershipId,
        {
          role_key:
            nextRole,
        },
      );


      onSaved?.(
        nextRole,
      );
    } catch (
      cause
    ) {
      setSelectedRole(
        value,
      );

      setError(
        cause instanceof Error
          ? cause.message
          : "Unable to update member role.",
      );
    } finally {
      setSaving(
        false,
      );
    }
  }


  const isDisabled =
    disabled ||
    saving ||
    !workspaceId ||
    !canAssign;


  return (
    <div
      style={{
        minWidth:
          130,
      }}
    >
      <div
        style={{
          position:
            "relative",
        }}
      >
        <select
          value={
            selectedRole
          }
          disabled={
            isDisabled
          }
          onChange={(
            event,
          ) => {
            const next =
              event.target
                .value;

            setSelectedRole(
              next,
            );

            void save(
              next,
            );
          }}
          style={{
            width:
              "100%",

            minHeight:
              34,

            padding:
              "6px 30px 6px 9px",

            border:
              "1px solid var(--color-border)",

            borderRadius:
              7,

            background:
              "#fff",

            fontSize:
              11,
          }}
        >
          {availableRoles.map(
            (
              role,
            ) => (
              <option
                key={
                  role.id ??
                  role.role_key
                }
                value={
                  role.role_key
                }
                disabled={
                  !role.is_active
                }
              >
                {
                  role.display_name
                }
              </option>
            ),
          )}
        </select>


        {saving ? (
          <Loader2
            size={
              13
            }
            style={{
              position:
                "absolute",

              right:
                9,

              top:
                10,

              pointerEvents:
                "none",
            }}
          />
        ) : null}
      </div>


      {error ? (
        <div
          style={{
            marginTop:
              4,

            color:
              "#a32b2b",

            fontSize:
              9,
          }}
        >
          {error}
        </div>
      ) : null}
    </div>
  );
}