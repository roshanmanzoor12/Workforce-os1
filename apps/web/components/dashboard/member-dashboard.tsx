"use client";

import {
  UserRound,
} from "lucide-react";

import {
  RoleAwareModuleGrid,
} from "@/components/dashboard/role-aware-module-grid";

import {
  useWorkspace,
} from "@/contexts/workspace-context";


export function MemberDashboard({
  client = false,
}: {
  client?:
    boolean;
}) {
  const {
    workspace,

    workspaceRole,

    effectivePermissions,
  } =
    useWorkspace();


  return (
    <div
      style={{
        display:
          "grid",

        gap:
          18,
      }}
    >
      <div>
        <div
          style={{
            display:
              "flex",

            alignItems:
              "center",

            gap:
              6,

            color:
              "#74787c",

            fontSize:
              10,

            fontWeight:
              600,
          }}
        >
          <UserRound
            size={
              13
            }
          />

          {client
            ? "Client / Guest Workspace"
            : "Employee Workspace"}
        </div>


        <h1
          style={{
            marginTop:
              5,
          }}
        >
          {workspace?.name ??
            "Workspace"}
        </h1>


        <p className="text-label">
          {client
            ? "Shared workspace resources available to your role."
            : "Your attendance, tasks, meetings, team and assigned workspace tools."}
        </p>
      </div>


      <section className="panel">
        <div
          className="panel-body"
          style={{
            display:
              "flex",

            justifyContent:
              "space-between",

            gap:
              20,

            padding:
              16,
          }}
        >
          <div>
            <span className="text-label">
              Role
            </span>

            <strong
              style={{
                display:
                  "block",

                marginTop:
                  4,
              }}
            >
              {workspaceRole
                ?.display_name ??
                (client
                  ? "Client"
                  : "Member")}
            </strong>
          </div>


          <div>
            <span className="text-label">
              Available Abilities
            </span>

            <strong
              style={{
                display:
                  "block",

                marginTop:
                  4,
              }}
            >
              {
                effectivePermissions.length
              }
            </strong>
          </div>
        </div>
      </section>


      <RoleAwareModuleGrid />
    </div>
  );
}