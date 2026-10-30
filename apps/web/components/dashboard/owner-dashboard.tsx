"use client";

import {
  ShieldCheck,
} from "lucide-react";

import {
  RoleAwareModuleGrid,
} from "@/components/dashboard/role-aware-module-grid";

import {
  RolePreviewSwitcher,
} from "@/components/workspace/role-preview-switcher";

import {
  useWorkspace,
} from "@/contexts/workspace-context";

export function OwnerDashboard() {
  const {
    workspace,

    workspaceRole,

    permissions,

    entitlements,
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
      <div
        style={{
          display:
            "flex",

          justifyContent:
            "space-between",

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
                "#a36e00",

              fontSize:
                10,

              fontWeight:
                600,
            }}
          >
            <ShieldCheck
              size={
                13
              }
            />

            Workspace Owner
          </div>

          <h1
            style={{
              marginTop:
                5,
            }}
          >
            {workspace?.name ??
              "Workspace"}{" "}
            Dashboard
          </h1>

          <p className="text-label">
            Full workspace administration and operations access.
          </p>
        </div>

        <RolePreviewSwitcher />
      </div>

      <div
        style={{
          display:
            "grid",

          gridTemplateColumns:
            "repeat(3, minmax(0, 1fr))",

          gap:
            12,
        }}
      >
        <InfoCard
          label="Role"
          value={
            workspaceRole
              ?.display_name ??
            "Owner"
          }
        />

        <InfoCard
          label="Permissions"
          value={
            permissions.includes(
              "*",
            )
              ? "Full access"
              : `${permissions.length} permissions`
          }
        />

        <InfoCard
          label="Plan"
          value={
            entitlements
              ?.plan_code ??
            "—"
          }
        />
      </div>

      <section>
        <h2
          style={{
            marginBottom:
              10,

            fontSize:
              14,
          }}
        >
          Workspace Modules
        </h2>

        <RoleAwareModuleGrid />
      </section>
    </div>
  );
}

function InfoCard({
  label,
  value,
}: {
  label:
    string;

  value:
    string;
}) {
  return (
    <section className="panel">
      <div
        className="panel-body"
        style={{
          padding:
            16,
        }}
      >
        <span
          className="text-label"
        >
          {label}
        </span>

        <strong
          style={{
            display:
              "block",

            marginTop:
              6,

            fontSize:
              17,
          }}
        >
          {value}
        </strong>
      </div>
    </section>
  );
}