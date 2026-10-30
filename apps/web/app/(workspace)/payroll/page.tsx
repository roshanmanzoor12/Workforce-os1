"use client";

import {
  CircleDollarSign,
  Download,
  Hourglass,
  MinusCircle,
  Plus,
  Users,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { MetricCard } from "@/components/ui/metric-card";
import { PageHeader } from "@/components/ui/page-header";
import { StatusBadge } from "@/components/ui/status-badge";

const payroll = [
  ["Marvin McKinney", "UI Mentor", "$7,850", "$8,080", "Paid"],
  ["Ralph Edwards", "UX Researcher", "$6,420", "$6,540", "Paid"],
  ["Dianne Russell", "Marketing Manager", "$5,980", "$6,110", "Paid"],
  ["Theresa Webb", "HR Specialist", "$4,760", "$4,800", "Pending"],
  ["Cameron Williamson", "Sales Executive", "$5,310", "$5,390", "Pending"],
  ["Devon Lane", "Front End Dev.", "$6,738", "$6,818", "Pending"],
];

export default function PayrollPage() {
  return (
    <div style={{ maxWidth: 1680, margin: "0 auto" }}>
      <PageHeader
        title="Payroll / Salary"
        description="Manage payroll runs, salaries, and compensation."
        actions={
          <>
            <Button variant="brand">
              <Plus size={15} />
              New Payroll Run
            </Button>

            <Button variant="outline">
              Add Adjustment
            </Button>

            <Button variant="outline">
              <Download size={15} />
              Export Report
            </Button>
          </>
        }
      />

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(5, minmax(0, 1fr))",
          gap: 12,
          marginBottom: 16,
        }}
      >
        <MetricCard label="Payroll This Month" value="$1,248,540" icon={<CircleDollarSign size={21} />} tone="brand" />
        <MetricCard label="Pending Approvals" value="23" icon={<Hourglass size={21} />} tone="warning" />
        <MetricCard label="Paid Employees" value="865" icon={<Users size={21} />} tone="success" />
        <MetricCard label="Total Deductions" value="$184,320" icon={<MinusCircle size={21} />} />
        <MetricCard label="Overtime Payout" value="$76,540" icon={<CircleDollarSign size={21} />} tone="brand" />
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "minmax(0, 1.6fr) minmax(320px, .9fr)",
          gap: 16,
        }}
      >
        <section className="panel" style={{ overflow: "hidden" }}>
          <div className="panel-header">
            <h2 className="text-section-title">
              Payroll Summary — May 2025
            </h2>

            <StatusBadge variant="info">
              In Progress
            </StatusBadge>
          </div>

          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Employee</th>
                  <th>Job Title</th>
                  <th>Base Salary</th>
                  <th>Net Salary</th>
                  <th>Status</th>
                </tr>
              </thead>

              <tbody>
                {payroll.map(([employee, role, base, net, status]) => (
                  <tr key={employee}>
                    <td>{employee}</td>
                    <td>{role}</td>
                    <td>{base}</td>
                    <td>{net}</td>
                    <td>
                      <StatusBadge
                        variant={
                          status === "Paid"
                            ? "success"
                            : "warning"
                        }
                      >
                        {status}
                      </StatusBadge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="panel">
          <div className="panel-header">
            <h2 className="text-section-title">
              Payroll Cashflow Trend
            </h2>
          </div>

          <div
            className="panel-body"
            style={{
              height: 360,
              display: "flex",
              alignItems: "flex-end",
              gap: 20,
            }}
          >
            {[64, 49, 61, 56, 59, 57, 82].map((value, index) => (
              <div
                key={index}
                style={{
                  flex: 1,
                  textAlign: "center",
                }}
              >
                <div
                  style={{
                    height: value * 2.5,
                    width: 10,
                    margin: "0 auto 10px",
                    background: "var(--color-brand)",
                    borderRadius: 999,
                  }}
                />
                <span className="text-label">
                  {["Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May"][index]}
                </span>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}