"use client";

import {
  Building2,
  Mail,
  UserRound,
} from "lucide-react";

import type {
  Employee,
} from "@/services/employees.service";


export interface EmployeeCardProps {
  employee:
    Employee;

  departmentName?:
    string | null;

  roleLabel?:
    string | null;

  onOpen?:
    () => void;
}


export function EmployeeCard({
  employee,
  departmentName,
  roleLabel,
  onOpen,
}: EmployeeCardProps) {
  return (
    <button
      type="button"
      onClick={
        onOpen
      }
      style={{
        display:
          "grid",

        width:
          "100%",

        minHeight:
          150,

        gap:
          12,

        padding:
          16,

        border:
          "1px solid var(--color-border)",

        borderRadius:
          10,

        background:
          "#fffefa",

        color:
          "inherit",

        cursor:
          onOpen
            ? "pointer"
            : "default",

        textAlign:
          "left",
      }}
    >
      <div
        style={{
          display:
            "flex",

          alignItems:
            "center",

          gap:
            10,
        }}
      >
        <span
          style={{
            display:
              "grid",

            width:
              38,

            height:
              38,

            placeItems:
              "center",

            borderRadius:
              "50%",

            background:
              "#f1eee7",
          }}
        >
          <UserRound
            size={
              16
            }
          />
        </span>


        <div
          style={{
            minWidth:
              0,
          }}
        >
          <strong
            style={{
              display:
                "block",

              overflow:
                "hidden",

              fontSize:
                12,

              whiteSpace:
                "nowrap",

              textOverflow:
                "ellipsis",
            }}
          >
            {
              employee.full_name
            }
          </strong>


          <div
            className="text-label"
            style={{
              marginTop:
                2,
            }}
          >
            {employee.job_title ??
              "Employee"}
          </div>
        </div>
      </div>


      <div
        style={{
          display:
            "grid",

          gap:
            7,

          fontSize:
            10,
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
          <Mail
            size={
              12
            }
          />

          <span>
            {employee.work_email ??
              "No work email"}
          </span>
        </div>


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
          <Building2
            size={
              12
            }
          />

          <span>
            {departmentName ??
              "No department"}
          </span>
        </div>
      </div>


      <div
        style={{
          display:
            "flex",

          justifyContent:
            "space-between",

          gap:
            10,

          marginTop:
            "auto",

          fontSize:
            9,

          textTransform:
            "capitalize",
        }}
      >
        <span>
          {
            employee.employment_status
          }
        </span>

        {roleLabel ? (
          <span>
            {
              roleLabel
            }
          </span>
        ) : null}
      </div>
    </button>
  );
}