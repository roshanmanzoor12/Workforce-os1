"use client";

import {
  X,
} from "lucide-react";

import {
  EmployeeCreateForm,
} from "@/components/employees/employee-create-form";

import type {
  Employee,
} from "@/services/employees.service";


interface AddEmployeeDrawerProps {
  open: boolean;

  employees: Employee[];

  onClose: () => void;

  onCreated: () => Promise<void>;
}


export function AddEmployeeDrawer({
  open,
  employees,
  onClose,
  onCreated,
}: AddEmployeeDrawerProps) {
  if (!open) {
    return null;
  }


  return (
    <div
      role="presentation"
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 1000,

        display: "flex",
        justifyContent: "flex-end",

        background:
          "rgba(29, 25, 20, 0.28)",
      }}
      onMouseDown={(event) => {
        if (
          event.target ===
          event.currentTarget
        ) {
          onClose();
        }
      }}
    >
      <aside
        role="dialog"
        aria-modal="true"
        aria-label="Add employee"
        style={{
          width:
            "min(760px, 96vw)",

          height: "100vh",

          overflowY: "auto",

          borderLeft:
            "1px solid var(--color-border)",

          background:
            "var(--color-app-background, #faf8f3)",

          boxShadow:
            "-16px 0 48px rgba(28, 24, 17, 0.14)",
        }}
      >
        <header
          style={{
            position: "sticky",
            top: 0,
            zIndex: 5,

            display: "flex",
            minHeight: 68,

            alignItems: "center",
            justifyContent:
              "space-between",

            gap: 16,

            padding:
              "0 20px",

            borderBottom:
              "1px solid var(--color-border)",

            background:
              "#fffefa",
          }}
        >
          <div>
            <strong
              style={{
                display: "block",
                fontSize: 15,
              }}
            >
              Add Employee
            </strong>

            <span
              className="text-label"
              style={{
                display: "block",
                marginTop: 3,
              }}
            >
              Create an employee and configure workspace access.
            </span>
          </div>


          <button
            type="button"
            aria-label="Close add employee"
            onClick={onClose}
            style={{
              display: "grid",

              width: 34,
              height: 34,

              placeItems: "center",

              border:
                "1px solid var(--color-border)",

              borderRadius: 8,

              background:
                "#fffefa",

              color:
                "#34373a",

              cursor: "pointer",
            }}
          >
            <X
              size={16}
            />
          </button>
        </header>


        <EmployeeCreateForm
          employees={employees}
          onCancel={onClose}
          onCreated={onCreated}
        />
      </aside>
    </div>
  );
}