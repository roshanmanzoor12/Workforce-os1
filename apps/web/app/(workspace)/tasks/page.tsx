"use client";

import { useState } from "react";

import {
  CheckCircle2,
  Circle,
  Plus,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { PageHeader } from "@/components/ui/page-header";
import { StatusBadge } from "@/components/ui/status-badge";

interface Task {
  id: number;
  title: string;
  owner: string;
  status: "Todo" | "In Progress" | "Done";
}

const initialTasks: Task[] = [
  {
    id: 1,
    title: "Complete workforce dashboard",
    owner: "Marvin",
    status: "In Progress",
  },
  {
    id: 2,
    title: "Review employee agent logs",
    owner: "Ralph",
    status: "Todo",
  },
  {
    id: 3,
    title: "Approve payroll run",
    owner: "Theresa",
    status: "Done",
  },
  {
    id: 4,
    title: "Update monitoring policies",
    owner: "Dianne",
    status: "Todo",
  },
];

export default function TasksPage() {
  const [tasks, setTasks] =
    useState(initialTasks);

  function addTask() {
    setTasks((current) => [
      ...current,
      {
        id: Date.now(),
        title: "New Task",
        owner: "Unassigned",
        status: "Todo",
      },
    ]);
  }

  function advanceTask(id: number) {
    setTasks((current) =>
      current.map((task) => {
        if (task.id !== id) {
          return task;
        }

        return {
          ...task,
          status:
            task.status === "Todo"
              ? "In Progress"
              : task.status ===
                  "In Progress"
                ? "Done"
                : "Done",
        };
      }),
    );
  }

  return (
    <div
      style={{
        maxWidth: 1400,
        margin: "0 auto",
      }}
    >
      <PageHeader
        title="Tasks"
        description="Organize work, assignments and team priorities."
        actions={
          <Button onClick={addTask}>
            <Plus size={15} />
            New Task
          </Button>
        }
      />

      <div
        style={{
          display: "grid",
          gridTemplateColumns:
            "repeat(3,1fr)",
          gap: 16,
        }}
      >
        {(
          [
            "Todo",
            "In Progress",
            "Done",
          ] as const
        ).map((column) => (
          <section
            className="panel"
            key={column}
          >
            <div className="panel-header">
              <h2 className="text-section-title">
                {column}
              </h2>

              <StatusBadge
                variant={
                  column === "Done"
                    ? "success"
                    : column ===
                        "In Progress"
                      ? "warning"
                      : "neutral"
                }
              >
                {
                  tasks.filter(
                    (task) =>
                      task.status === column,
                  ).length
                }
              </StatusBadge>
            </div>

            <div className="panel-body">
              {tasks
                .filter(
                  (task) =>
                    task.status === column,
                )
                .map((task) => (
                  <button
                    key={task.id}
                    type="button"
                    onClick={() =>
                      advanceTask(task.id)
                    }
                    style={{
                      display: "block",
                      width: "100%",
                      padding: 14,
                      marginBottom: 10,
                      border:
                        "1px solid var(--color-border)",
                      borderRadius: 8,
                      background:
                        "var(--color-surface)",
                      textAlign: "left",
                      cursor: "pointer",
                    }}
                  >
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: 8,
                      }}
                    >
                      {task.status ===
                      "Done" ? (
                        <CheckCircle2
                          size={16}
                          color="var(--color-success)"
                        />
                      ) : (
                        <Circle size={16} />
                      )}

                      <strong
                        style={{
                          fontSize: 12,
                        }}
                      >
                        {task.title}
                      </strong>
                    </div>

                    <div
                      className="text-label"
                      style={{
                        marginTop: 8,
                      }}
                    >
                      {task.owner}
                    </div>
                  </button>
                ))}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}