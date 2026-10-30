"use client";

import {
  Blocks,
  CheckCircle2,
  ExternalLink,
  MoreHorizontal,
} from "lucide-react";

export interface IntegrationCardData {
  id: string;
  name: string;
  description: string;
  category: string;
  status:
    | "available"
    | "connected"
    | "unavailable";
  accent?: string;
}

interface IntegrationCardProps {
  integration: IntegrationCardData;
  onManage?: (
    integration: IntegrationCardData,
  ) => void;
}

export function IntegrationCard({
  integration,
  onManage,
}: IntegrationCardProps) {
  const statusLabel =
    integration.status ===
    "connected"
      ? "Connected"
      : integration.status ===
        "unavailable"
        ? "Unavailable"
        : "Available";

  return (
    <article
      style={{
        display: "grid",
        gap: 15,
        padding: 16,
        border:
          "1px solid var(--color-border)",
        borderRadius: 11,
        background:
          "var(--color-surface)",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems:
            "flex-start",
          justifyContent:
            "space-between",
          gap: 12,
        }}
      >
        <div
          style={{
            width: 38,
            height: 38,
            display: "grid",
            placeItems: "center",
            borderRadius: 9,
            background:
              "var(--color-muted)",
          }}
        >
          <Blocks
            size={18}
          />
        </div>

        <button
          type="button"
          onClick={() =>
            onManage?.(
              integration,
            )
          }
          disabled={
            !onManage ||
            integration.status ===
              "unavailable"
          }
          aria-label={`${integration.name} actions`}
          style={{
            width: 34,
            height: 34,
            display: "grid",
            placeItems: "center",
            border:
              "1px solid var(--color-border)",
            borderRadius: 8,
            background:
              "var(--color-surface)",
            cursor:
              !onManage ||
              integration.status ===
                "unavailable"
                ? "not-allowed"
                : "pointer",
          }}
        >
          <MoreHorizontal
            size={16}
          />
        </button>
      </div>

      <div>
        <h3
          style={{
            margin: 0,
            fontSize: 14,
          }}
        >
          {integration.name}
        </h3>

        <p
          className="text-label"
          style={{
            margin:
              "5px 0 0",
            lineHeight: 1.5,
          }}
        >
          {
            integration.description
          }
        </p>
      </div>

      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent:
            "space-between",
          gap: 10,
          paddingTop: 2,
        }}
      >
        <span
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 6,
            fontSize: 11,
            fontWeight: 650,
          }}
        >
          <span
            style={{
              width: 7,
              height: 7,
              borderRadius:
                "50%",
              background:
                integration.status ===
                "connected"
                  ? "#16794c"
                  : integration.status ===
                    "unavailable"
                    ? "#a12b26"
                    : "#8b6b00",
            }}
          />

          {statusLabel}
        </span>

        {integration.status ===
        "connected" ? (
          <CheckCircle2
            size={15}
          />
        ) : (
          <ExternalLink
            size={15}
            style={{
              opacity: 0.5,
            }}
          />
        )}
      </div>

      <span
        className="text-label"
        style={{
          fontSize: 10,
        }}
      >
        {integration.category}
      </span>
    </article>
  );
}