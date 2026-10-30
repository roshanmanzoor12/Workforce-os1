"use client";

import {
  Plus,
  RefreshCcw,
} from "lucide-react";

import {
  useCallback,
  useEffect,
  useState,
} from "react";

import {
  useRouter,
  useSearchParams,
} from "next/navigation";

import {
  AddEmployeeDrawer,
} from "@/components/employees/add-employee-drawer";

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


export function OwnerEmployeeView() {
  const router =
    useRouter();


  const searchParams =
    useSearchParams();


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
    useState(true);


  const [
    error,
    setError,
  ] =
    useState<string | null>(
      null,
    );


  const [
    createOpen,
    setCreateOpen,
  ] =
    useState(false);


  const load =
    useCallback(
      async () => {
        if (!workspaceId) {
          setLoading(
            false,
          );

          return;
        }


        const currentWorkspaceId =
          workspaceId;


        try {
          setLoading(
            true,
          );

          setError(
            null,
          );


          const [
            employeesResponse,
            departmentsResponse,
          ] =
            await Promise.all([
              employeesService.list(
                currentWorkspaceId,
              ),

              departmentsService.list(
                currentWorkspaceId,
              ),
            ]);


          setEmployees(
            employeesResponse.employees,
          );


          setDepartments(
            departmentsResponse.departments,
          );
        } catch (cause) {
          setError(
            cause instanceof Error
              ? cause.message
              : "Unable to load employees.",
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


  useEffect(() => {
    void load();
  }, [
    load,
  ]);


  useEffect(() => {
    const shouldCreate =
      searchParams.get(
        "create",
      ) === "1";


    if (
      shouldCreate
    ) {
      setCreateOpen(
        true,
      );
    }
  }, [
    searchParams,
  ]);


  function openCreateDrawer() {
    setCreateOpen(
      true,
    );


    router.replace(
      "/employees?create=1",
      {
        scroll: false,
      },
    );
  }


  function closeCreateDrawer() {
    setCreateOpen(
      false,
    );


    router.replace(
      "/employees",
      {
        scroll: false,
      },
    );
  }


  async function handleCreated() {
    setCreateOpen(
      false,
    );


    router.replace(
      "/employees",
      {
        scroll: false,
      },
    );


    await load();
  }


  return (
    <>
      <div
        style={{
          display: "grid",
          gap: 18,
        }}
      >
        <div
          style={{
            display: "flex",

            alignItems:
              "flex-start",

            justifyContent:
              "space-between",

            gap: 14,
          }}
        >
          <div>
            <h1>
              Employees
            </h1>


            <p
              className="text-label"
              style={{
                marginTop: 5,
              }}
            >
              Full employee directory for{" "}
              {workspace?.name ??
                "this workspace"}.
            </p>
          </div>


          <div
            style={{
              display: "flex",
              gap: 8,
            }}
          >
            <Button
              variant="outline"
              disabled={
                loading
              }
              onClick={() => {
                void load();
              }}
            >
              <RefreshCcw
                size={14}
              />

              Refresh
            </Button>


            <Button
              onClick={
                openCreateDrawer
              }
            >
              <Plus
                size={14}
              />

              Add Employee
            </Button>
          </div>
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
              height: 420,
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
            title="All Employees"
            description="Owner workspace employee access."
          />
        )}
      </div>


      <AddEmployeeDrawer
        open={
          createOpen
        }
        employees={
          employees
        }
        onClose={
          closeCreateDrawer
        }
        onCreated={
          handleCreated
        }
      />
    </>
  );
}