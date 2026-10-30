"use client";

import {
  ClientEmployeeView,
} from "@/components/employees/client-employee-view";

import {
  ManagerEmployeeView,
} from "@/components/employees/manager-employee-view";

import {
  MemberEmployeeView,
} from "@/components/employees/member-employee-view";

import {
  OwnerEmployeeView,
} from "@/components/employees/owner-employee-view";

import {
  WorkspaceRequired,
} from "@/components/workspace/workspace-required";

import {
  useWorkspace,
} from "@/contexts/workspace-context";

import {
  canViewEmployees,
} from "@/components/employees/employee-access";


export default function EmployeesPage() {
  const {
    navigationView,

    effectiveNavigationView,

    effectivePermissions,
  } =
    useWorkspace();


  const allowed =
    canViewEmployees(
      effectivePermissions,
      effectiveNavigationView,
    );


  return (
    <WorkspaceRequired>
      {!allowed ? (
        <section className="panel">
          <div
            className="panel-body"
            style={{
              minHeight:
                300,

              display:
                "grid",

              placeItems:
                "center",

              padding:
                36,

              textAlign:
                "center",
            }}
          >
            <div>
              <h2>
                Employee access unavailable
              </h2>

              <p
                className="text-label"
                style={{
                  maxWidth:
                    460,

                  margin:
                    "7px auto 0",
                }}
              >
                Your current workspace role does not include employee-directory access.
              </p>
            </div>
          </div>
        </section>
      ) : navigationView ===
          "owner" ||
        effectiveNavigationView ===
          "owner" ||
        effectiveNavigationView ===
          "admin" ? (
        <OwnerEmployeeView />
      ) : effectiveNavigationView ===
        "manager" ? (
        <ManagerEmployeeView />
      ) : effectiveNavigationView ===
        "client" ? (
        <ClientEmployeeView />
      ) : (
        <MemberEmployeeView />
      )}
    </WorkspaceRequired>
  );
}