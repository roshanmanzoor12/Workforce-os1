"use client";

import { Filter } from "lucide-react";

import { Button } from "@/components/ui/button";
import { SearchInput } from "@/components/ui/search-input";

export interface EmployeeFilterState {
  search: string;
  status: string;
  department: string;
}

interface EmployeeFiltersProps {
  value: EmployeeFilterState;
  departments?: string[];
  disabled?: boolean;
  onChange: (
    next: EmployeeFilterState,
  ) => void;
}

export function EmployeeFilters({
  value,
  departments = [],
  disabled = false,
  onChange,
}: EmployeeFiltersProps) {
  function update<
    K extends keyof EmployeeFilterState,
  >(
    key: K,
    nextValue: EmployeeFilterState[K],
  ) {
    onChange({
      ...value,
      [key]: nextValue,
    });
  }

  function clearFilters() {
    onChange({
      search: "",
      status: "",
      department: "",
    });
  }

  const hasFilters =
    Boolean(value.search) ||
    Boolean(value.status) ||
    Boolean(value.department);

  return (
    <section className="filter-toolbar">
      <div className="filter-toolbar__search">
        <SearchInput
          value={value.search}
          disabled={disabled}
          placeholder="Search employees"
          onChange={(search) =>
            update("search", search)
          }
        />
      </div>

      <div className="filter-toolbar__field">
        <label className="field">
          <span className="field-label">
            Status
          </span>

          <select
            className="select"
            value={value.status}
            disabled={disabled}
            onChange={(event) =>
              update(
                "status",
                event.target.value,
              )
            }
          >
            <option value="">
              All statuses
            </option>
            <option value="active">
              Active
            </option>
            <option value="inactive">
              Inactive
            </option>
          </select>
        </label>
      </div>

      <div className="filter-toolbar__field">
        <label className="field">
          <span className="field-label">
            Department
          </span>

          <select
            className="select"
            value={value.department}
            disabled={disabled}
            onChange={(event) =>
              update(
                "department",
                event.target.value,
              )
            }
          >
            <option value="">
              All departments
            </option>

            {departments.map(
              (department) => (
                <option
                  key={department}
                  value={department}
                >
                  {department}
                </option>
              ),
            )}
          </select>
        </label>
      </div>

      <Button
        variant="outline"
        disabled={disabled || !hasFilters}
        onClick={clearFilters}
      >
        <Filter
          size={15}
          strokeWidth={1.8}
        />
        Clear
      </Button>
    </section>
  );
}