"use client";

import { useState } from "react";

import {
  CalendarDays,
  Check,
  Clock3,
  Plus,
  X,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { MetricCard } from "@/components/ui/metric-card";
import { PageHeader } from "@/components/ui/page-header";
import { StatusBadge } from "@/components/ui/status-badge";

interface LeaveRequest {
  id: number;
  employee: string;
  type: string;
  dates: string;
  status:
    | "Pending"
    | "Approved"
    | "Rejected";
}

const initialRequests: LeaveRequest[] = [
  {
    id: 1,
    employee: "Ralph Edwards",
    type: "Annual Leave",
    dates: "May 20 - May 22",
    status: "Pending",
  },
  {
    id: 2,
    employee: "Theresa Webb",
    type: "Sick Leave",
    dates: "May 18",
    status: "Approved",
  },
  {
    id: 3,
    employee: "Devon Lane",
    type: "Personal Leave",
    dates: "May 24",
    status: "Pending",
  },
];

export default function LeavePage() {
  const [requests, setRequests] =
    useState(initialRequests);

  function updateStatus(
    id: number,
    status: LeaveRequest["status"],
  ) {
    setRequests((current) =>
      current.map((request) =>
        request.id === id
          ? {
              ...request,
              status,
            }
          : request,
      ),
    );
  }

  return (
    <div
      style={{
        maxWidth: 1450,
        margin: "0 auto",
      }}
    >
      <PageHeader
        title="Leave Management"
        description="Manage employee leave balances, requests and approvals."
        actions={
          <Button>
            <Plus size={15} />
            Request Leave
          </Button>
        }
      />

      <div
        className="metric-grid"
        style={{ marginBottom: 16 }}
      >
        <MetricCard
          label="Annual Leave"
          value="142"
          icon={
            <CalendarDays size={21} />
          }
          tone="brand"
        />
        <MetricCard
          label="Sick Leave"
          value="28"
          icon={<Clock3 size={21} />}
        />
        <MetricCard
          label="Pending Requests"
          value={
            requests.filter(
              (request) =>
                request.status ===
                "Pending",
            ).length
          }
          icon={<Clock3 size={21} />}
          tone="warning"
        />
        <MetricCard
          label="Approved"
          value={
            requests.filter(
              (request) =>
                request.status ===
                "Approved",
            ).length
          }
          icon={<Check size={21} />}
          tone="success"
        />
      </div>

      <section
        className="panel"
        style={{ overflow: "hidden" }}
      >
        <div className="panel-header">
          <h2 className="text-section-title">
            Leave Requests
          </h2>
        </div>

        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Employee</th>
                <th>Leave Type</th>
                <th>Dates</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>

            <tbody>
              {requests.map((request) => (
                <tr key={request.id}>
                  <td>
                    {request.employee}
                  </td>
                  <td>{request.type}</td>
                  <td>{request.dates}</td>
                  <td>
                    <StatusBadge
                      variant={
                        request.status ===
                        "Approved"
                          ? "success"
                          : request.status ===
                              "Rejected"
                            ? "danger"
                            : "warning"
                      }
                    >
                      {request.status}
                    </StatusBadge>
                  </td>

                  <td>
                    {request.status ===
                    "Pending" ? (
                      <div
                        style={{
                          display: "flex",
                          gap: 6,
                        }}
                      >
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() =>
                            updateStatus(
                              request.id,
                              "Approved",
                            )
                          }
                        >
                          <Check
                            size={14}
                          />
                          Approve
                        </Button>

                        <Button
                          size="sm"
                          variant="danger"
                          onClick={() =>
                            updateStatus(
                              request.id,
                              "Rejected",
                            )
                          }
                        >
                          <X size={14} />
                          Reject
                        </Button>
                      </div>
                    ) : (
                      "—"
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}