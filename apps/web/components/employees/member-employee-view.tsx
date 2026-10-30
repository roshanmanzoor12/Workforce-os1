"use client";

import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  EmployeeDirectory,
} from "@/components/employees/employee-directory";

import {
  useWorkspace,
} from "@/contexts/workspace-context";

import {
  departmentsService,
  type Department,
} from "@/services/departments.service";

import {
  employeesService,
  type Employee,
} from "@/services/employees.service";


export function MemberEmployeeView() {
  const {
    workspaceId,
    workspace,
    user,
  } =
    useWorkspace();


  const [
    employees,
    setEmployees,
  ] =
    useState<Employee[]>(
      [],
    );


  const [
    departments,
    setDepartments,
  ] =
    useState<Department[]>(
      [],
    );


  const [
    loading,
    setLoading,
  ] =
    useState(
      true,
    );


  const [
    error,
    setError,
  ] =
    useState<string | null>(
      null,
    );


  const load =
    useCallback(
      async () => {
        if (
          !workspaceId
        ) {
          return;
        }


        try {
          setLoading(
            true,
          );

          setError(
            null,
          );


          const [
            employeeResponse,
            departmentResponse,
          ] =
            await Promise.all([
              employeesService.list(
                workspaceId,
              ),

              departmentsService.list(
                workspaceId,
              ),
            ]);


          setEmployees(
            employeeResponse.employees,
          );

          setDepartments(
            departmentResponse.departments,
          );

        } catch (
          cause
        ) {
          setError(
            cause instanceof Error
              ? cause.message
              : "Unable to load employee information.",
          );

        } finally {
          setLoading(
            false,
          );
        }
      },
      [
        workspaceId,
      ],
    );


  useEffect(
    () => {
      void load();
    },
    [
      load,
    ],
  );


  const visible =
    useMemo(
      () => {
        if (
          !user
        ) {
          return employees;
        }


        const own =
          employees.filter(
            (employee) =>
              employee.work_email
                ?.toLowerCase() ===
              user.email
                .toLowerCase(),
          );


        /*
         * If backend already returns the member's permitted
         * team set, retain it. Otherwise, when own employee
         * can be identified, present own record.
         */
        return own.length >
          0
          ? own
          : employees;
      },
      [
        employees,
        user,
      ],
    );


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
        <h1>
          My Team
        </h1>

        <p
          className="text-label"
          style={{
            marginTop:
              5,
          }}
        >
          Employee information available to your role in{" "}
          {workspace?.name ??
            "this workspace"}.
        </p>
      </div>


      {error ? (
        <div className="auth-error">
          {error}
        </div>
      ) : null}


      {loading ? (
        <div
          className="skeleton"
          style={{
            height:
              360,
          }}
        />
      ) : (
        <EmployeeDirectory
          employees={
            visible
          }
          departments={
            departments
          }
          title="Available People"
          description="Only records permitted by your workspace role should be returned by the backend."
        />
      )}
    </div>
  );
}