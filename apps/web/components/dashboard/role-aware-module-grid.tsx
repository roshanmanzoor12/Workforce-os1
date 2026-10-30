"use client";

import Link from "next/link";

import {
  LockKeyhole,
} from "lucide-react";

import {
  useWorkspace,
} from "@/contexts/workspace-context";

import {
  hasAnyPermission,
} from "@/lib/workspace/access";

import {
  getWorkspaceNavigation,
} from "@/lib/workspace/navigation";


export function RoleAwareModuleGrid() {
  const {
    effectiveNavigationView,

    effectivePermissions,

    canUseMonitoring,
  } =
    useWorkspace();


  const modules =
    getWorkspaceNavigation(
      effectiveNavigationView,
    );


  return (
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
      {modules.map(
        (
          item,
        ) => {
          const allowed =
            !item.anyPermissions ||
            hasAnyPermission(
              effectivePermissions,
              item.anyPermissions,
              effectiveNavigationView,
            );


          const entitlementBlocked =
            item.entitlement ===
              "monitoring" &&
            !canUseMonitoring;


          const enabled =
            allowed &&
            !entitlementBlocked;


          const Icon =
            item.icon;


          if (
            !allowed &&
            effectiveNavigationView !==
              "owner"
          ) {
            return null;
          }


          const content = (
            <div
              style={{
                display:
                  "grid",

                minHeight:
                  120,

                alignContent:
                  "space-between",

                gap:
                  18,

                padding:
                  16,

                border:
                  "1px solid var(--color-border)",

                borderRadius:
                  9,

                background:
                  "#fffefa",

                opacity:
                  enabled
                    ? 1
                    : 0.62,
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
                }}
              >
                <Icon
                  size={
                    19
                  }
                />


                {!enabled ? (
                  <LockKeyhole
                    size={
                      14
                    }
                  />
                ) : null}
              </div>


              <div>
                <strong
                  style={{
                    display:
                      "block",

                    fontSize:
                      12,
                  }}
                >
                  {
                    item.label
                  }
                </strong>


                <span
                  style={{
                    display:
                      "block",

                    marginTop:
                      4,

                    color:
                      "#777b80",

                    fontSize:
                      10,
                  }}
                >
                  {entitlementBlocked
                    ? "Current plan does not include this feature."
                    : enabled
                      ? "Open module"
                      : "Permission required"}
                </span>
              </div>
            </div>
          );


          if (
            !enabled
          ) {
            return (
              <div
                key={
                  item.key
                }
              >
                {content}
              </div>
            );
          }


          return (
            <Link
              key={
                item.key
              }
              href={
                item.href
              }
              style={{
                color:
                  "inherit",

                textDecoration:
                  "none",
              }}
            >
              {content}
            </Link>
          );
        },
      )}
    </div>
  );
}