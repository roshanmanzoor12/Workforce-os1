"use client";

import {
  RefreshCcw,
} from "lucide-react";

import {
  useCallback,
  useEffect,
  useState,
} from "react";

import {
  EmployeeDirectory,
} from "@/components/employees/employee-directory";

import {
  Button,
} from "@/components/ui/button";

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


export function ManagerEmployeeView() {
  const {
    workspaceId,
    workspace,
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


          /*
           * Backend remains responsible for team scoping.
           * Frontend must not simulate security by filtering
           * a workspace-wide response itself.
           */
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
              : "Unable to load team members.",
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
            14,
        }}
      >
        <div>
          <h1>
            Team Members
          </h1>

          <p
            className="text-label"
            style={{
              marginTop:
                5,
            }}
          >
            People available to your manager role in{" "}
            {workspace?.name ??
              "this workspace"}.
          </p>
        </div>


        <Button
          variant="outline"
          onClick={() => {
            void load();
          }}
        >
          <RefreshCcw
            size={
              14
            }
          />

          Refresh
        </Button>
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
              420,
          }}
        />
      ) : (
        <EmployeeDirectory
          employees={
            employees
          }
          departments={
            departments
          }
          title="My Team"
          description="The backend controls which employee records this role can read."
        />
      )}
    </div>
  );
}