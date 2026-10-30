"use client";

import {
  Search,
} from "lucide-react";

import {
  useMemo,
  useState,
} from "react";

import {
  EmployeeCard,
} from "@/components/employees/employee-card";

import type {
  Department,
} from "@/services/departments.service";

import type {
  Employee,
} from "@/services/employees.service";


interface EmployeeDirectoryProps {
  employees:
    Employee[];

  departments:
    Department[];

  title:
    string;

  description:
    string;
}


export function EmployeeDirectory({
  employees,
  departments,
  title,
  description,
}: EmployeeDirectoryProps) {
  const [
    search,
    setSearch,
  ] =
    useState(
      "",
    );


  const departmentMap =
    useMemo(
      () =>
        new Map(
          departments.map(
            (department) => [
              department.id,
              department.name,
            ],
          ),
        ),
      [
        departments,
      ],
    );


  const filtered =
    useMemo(
      () => {
        const query =
          search
            .trim()
            .toLowerCase();


        if (
          !query
        ) {
          return employees;
        }


        return employees.filter(
          (employee) =>
            employee.full_name
              .toLowerCase()
              .includes(
                query,
              ) ||
            (
              employee.work_email ??
              ""
            )
              .toLowerCase()
              .includes(
                query,
              ) ||
            (
              employee.job_title ??
              ""
            )
              .toLowerCase()
              .includes(
                query,
              ) ||
            employee.employee_code
              .toLowerCase()
              .includes(
                query,
              ),
        );
      },
      [
        employees,
        search,
      ],
    );


  return (
    <div
      style={{
        display:
          "grid",

        gap:
          14,
      }}
    >
      <div>
        <h2
          style={{
            fontSize:
              15,
          }}
        >
          {title}
        </h2>

        <p
          className="text-label"
          style={{
            marginTop:
              4,
          }}
        >
          {description}
        </p>
      </div>


      <div
        style={{
          position:
            "relative",

          width:
            340,

          maxWidth:
            "100%",
        }}
      >
        <Search
          size={
            14
          }
          style={{
            position:
              "absolute",

            top:
              "50%",

            left:
              11,

            color:
              "#8c8f93",

            transform:
              "translateY(-50%)",
          }}
        />


        <input
          type="search"
          value={
            search
          }
          onChange={(
            event,
          ) =>
            setSearch(
              event.target.value,
            )
          }
          placeholder="Search employees"
          style={{
            width:
              "100%",

            height:
              38,

            padding:
              "0 12px 0 34px",

            border:
              "1px solid var(--color-border)",

            borderRadius:
              8,

            background:
              "#fffefa",

            outline:
              "none",
          }}
        />
      </div>


      {filtered.length ===
      0 ? (
        <section className="panel">
          <div
            className="panel-body"
            style={{
              padding:
                36,

              textAlign:
                "center",
            }}
          >
            <strong>
              No employees found
            </strong>

            <div
              className="text-label"
              style={{
                marginTop:
                  6,
              }}
            >
              No employee matches the current search.
            </div>
          </div>
        </section>
      ) : (
        <div
          style={{
            display:
              "grid",

            gridTemplateColumns:
              "repeat(auto-fill, minmax(250px, 1fr))",

            gap:
              12,
          }}
        >
          {filtered.map(
            (
              employee,
            ) => (
              <EmployeeCard
                key={
                  employee.id
                }
                employee={
                  employee
                }
                departmentName={
                  employee.department_id
                    ? departmentMap.get(
                        employee.department_id,
                      ) ??
                      "Department"
                    : null
                }
              />
            ),
          )}
        </div>
      )}
    </div>
  );
}