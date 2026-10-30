"use client";

import {
  Users,
} from "lucide-react";

import {
  RoleAwareModuleGrid,
} from "@/components/dashboard/role-aware-module-grid";

import {
  useWorkspace,
} from "@/contexts/workspace-context";


export function ManagerDashboard() {
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
              "#8e6700",

            fontSize:
              10,

            fontWeight:
              600,
          }}
        >
          <Users
            size={
              13
            }
          />

          Manager / Senior View
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
          Team and department tools available to your assigned role.
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
              Current Role
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
                "Manager"}
            </strong>
          </div>


          <div>
            <span className="text-label">
              Assigned Abilities
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